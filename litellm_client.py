import requests
from typing import Dict, Optional, Any
from datetime import datetime, timezone


class LiteLLMClient:
    def __init__(self, api_url: str, master_key: str):
        self.api_url = api_url.rstrip('/')
        self.master_key = master_key
        self.headers = {
            'Authorization': f'Bearer {master_key}',
            'Content-Type': 'application/json'
        }

    def list_users(self, page_size: int = 25) -> Dict[str, Any]:

        all_users = []
        for page in range(1, 1000, 1):
            url = f'{self.api_url}/user/list'
            print(page)
            try:
                response = requests.get(url, headers=self.headers, timeout=30,
                                        params={"page": page, "page_size": page_size})
                response.raise_for_status()

                # /user/list typically returns a list of user objects directly
                # or wrapped in a "users" key depending on version/config.
                resp_data = response.json()

                # Handle potential response formats (list vs dict wrapper)
                if isinstance(resp_data, list):
                    users = resp_data
                elif isinstance(resp_data, dict):
                    # Common keys for list wrappers: 'users', 'data', 'info'
                    users = resp_data.get('users') or resp_data.get('data') or []
                else:
                    users = []

            except requests.exceptions.RequestException as e:
                return {
                    'success': False,
                    'error': str(e),
                    'status_code': getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
                }
            all_users.extend(users)
            if len(users) < page_size or not users:
                break

        return all_users

    def list_teams(self) -> Dict[str, Any]:
        """
        List all teams in LiteLLM.

        Returns:
            List of teams found in LiteLLM.
        """
        url = f'{self.api_url}/team/list'

        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return {
                'success': True,
                'data': response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            }


    def get_team_id_by_name(self, team_name: str) -> Optional[str]:
        """
        Get team_id for a given team name (team_alias).

        Args:
            team_name: The name/alias of the team to find.

        Returns:
            The team_id if found, None otherwise.
        """
        # Reuse the list_teams method from previous step
        result = self.list_teams()

        if not result.get('success'):
            return None

        teams = result.get('data', [])

        # Handle case where data might be wrapped
        if isinstance(teams, dict) and 'teams' in teams:
            teams = teams['teams']

        target_name = team_name.lower().strip()

        for team in teams:
            # Check team_alias field
            alias = team.get('team_alias', '')
            if alias and alias.lower().strip() == target_name:
                return team.get('team_id')

        return None


    def team_exists(self, team_id: Optional[str] = None, team_name: Optional[str] = None) -> bool:
        """
        Check if a team exists by team_id OR team_name (alias).

        Args:
            team_id: The specific UUID of the team.
            team_name: The human-readable alias of the team.

        Returns:
            Dict with 'exists' (bool), 'found_by' ('id'|'name'|None), and 'data'.

        Raises:
            ValueError: If both team_id and team_name are None.
        """
        if not team_id and not team_name:
            raise ValueError("At least one of 'team_id' or 'team_name' must be provided.")

        # 1. Check by ID if provided (Most efficient: O(1))
        if team_id:
            url = f'{self.api_url}/team/info'
            try:
                response = requests.get(
                    url,
                    params={'team_id': team_id},
                    headers=self.headers,
                    timeout=10
                )
                if response.status_code == 200:
                    return True
            except requests.exceptions.RequestException:
                # If ID check fails (network or 404), continue to name check if provided
                pass

        # 2. Check by Name if provided (Scan: O(N))
        # Only runs if team_id was None OR team_id lookup returned 404
        if team_name:

            try:
                existing_teams = self.list_teams()

                # Normalize list structure
                if isinstance(existing_teams, dict):
                    teams = existing_teams.get('teams') or existing_teams.get('data') or []
                elif isinstance(existing_teams, list):
                    teams = existing_teams
                else:
                    teams = []

                target_alias = team_name.lower().strip()

                for team in teams:
                    # 'team_alias' is the field for team name in LiteLLM
                    alias = team.get('team_alias', '')
                    if alias and alias.lower().strip() == target_alias:
                        return True
            except requests.exceptions.RequestException as e:
                return {'success': False, 'exists': None, 'error': str(e)}

        return False

    def user_exists(self, email: str) -> bool:
        """
        Check if a user exists by fetching all users and searching for the email.

        Args:
            email: User's email address to search for

        Returns:
            Boolean indicating whether or not the user exists.
        """

        user_info = self.get_user_info(email=email)

        return user_info is not None



    def create_user(self, email: str, team_name: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Create a new user in LiteLLM, optionally adding them to a team by name.

        Args:
            email: User's email address
            team_name: Optional name of the team to add the user to.
            **kwargs: Additional parameters like user_role, max_budget, etc.

        Returns:
            Response from LiteLLM API
        """
        # 1. Resolve team_name to team_id if provided
        team_id = None
        if team_name:
            if self.team_exists(team_name=team_name):
                team_id = self.get_team_id_by_name(team_name=team_name)
                kwargs.setdefault('teams', []).append(team_id)
            else:
                # Optional: Fail if team name is invalid, or just warn/proceed
                # Here we return an error for clarity
                return {
                    'success': False,
                    'error': f"Team with name '{team_name}' not found."
                }

        # 2. Proceed with user creation
        url = f'{self.api_url}/user/new'
        data = {
            'user_email': email,
            'teams': [team_id] if team_id else [],
            **kwargs
        }

        response = requests.post(url, json=data, headers=self.headers, timeout=30)
        response.raise_for_status()
        return {
            'success': True,
            'data': response.json()
        }



    def create_token(self, email: str, models: Optional[list] = None, **kwargs) -> Dict[str, Any]:
        """
        Create a new access token (virtual key) for a user.
        
        Args:
            email: User's email address
            models: List of models the key can access
            **kwargs: Additional parameters like duration, max_budget, etc.
        
        Returns:
            Response from LiteLLM API
        """
        url = f'{self.api_url}/key/generate'
        user_id = self.get_user_id_by_email(email=email)
        data = {
            'metadata': {'user': email},
            'user_id': user_id,
            **kwargs
        }
        
        if models:
            data['models'] = models
        
        try:
            response = requests.post(url, json=data, headers=self.headers, timeout=30)
            response.raise_for_status()
            return {
                'success': True,
                'data': response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            }

    def get_user_info(self, user_id: str = None, email: str = None) -> Dict[str, Any] | None:
        """
        Get information about a user.
        
        Args:
            user_id: User ID
            email: User's email address
        
        Returns:
            Response from LiteLLM API
        """
        if not user_id and not email:
            raise ValueError("At least one of 'user_id' or 'email' must be provided.")

        if user_id:

            url = f'{self.api_url}/user/info'
            params = {'user_id': user_id}

            response = requests.get(url, params=params, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        else:

            users = self.list_users()
            # Normalize email for comparison
            target_email = email.lower().strip()
            for user in users:
                # Check user_email field (standard LiteLLM user object field)
                user_email = user.get('user_email', '')
                if user_email and user_email.lower().strip() == target_email:
                    return user

        return None



    def get_key_info(self, key: str) -> Dict[str, Any]:
        """
        Get information about a key.
        
        Args:
            key: API key
        
        Returns:
            Response from LiteLLM API
        """
        url = f'{self.api_url}/key/info'
        params = {'key': key}

        response = requests.get(url, params=params, headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.json()


    def get_user_id_by_email(self, email: str) -> Optional[str]:
        """
        Get the LiteLLM user_id for a given email address.

        Args:
            email: User's email address

        Returns:
            The user_id string if found, None otherwise.
        """
        # Reuse existing user_exists logic but return the ID specifically
        user_info = self.get_user_info(email=email)
        return user_info.get('user_id')

    def list_user_keys(self, user_id: str) -> Dict[str, Any]:
        """
        List all keys associated with a specific user_id.

        Args:
            user_id: The unique LiteLLM user ID

        Returns:
            Dict containing success status and list of keys
        """
        url = f'{self.api_url}/key/list'
        params = {'user_id': user_id}

        try:
            response = requests.get(url, params=params, headers=self.headers, timeout=30)
            response.raise_for_status()

            resp_data = response.json()

            # Handle potential response wrappers (keys, data, or raw list)
            if isinstance(resp_data, list):
                keys = resp_data
            elif isinstance(resp_data, dict):
                keys = resp_data.get('keys') or resp_data.get('data') or []
            else:
                keys = []

            return {
                'success': True,
                'count': len(keys),
                'data': keys
            }

        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            }


    def get_active_tokens(self, email: str) -> Dict[str, Any]:
        """
        Get all active (unexpired) tokens for a user by their email.
        Uses standard library only (no dateutil dependency).
        """
        # 1. Resolve email to user_id
        user_id = self.get_user_id_by_email(email=email)
        if not user_id:
            return {
                'success': False,
                'error': f"User with email '{email}' not found."
            }

        # 2. Get all keys for this user_id
        keys_result = self.list_user_keys(user_id)
        if not keys_result.get('success'):
            return keys_result

        all_keys = keys_result.get('data', [])
        active_tokens = []

        # Use timezone-aware UTC for comparison
        now = datetime.now(timezone.utc)

        # 3. Filter for unexpired keys
        for key in all_keys:
            key_info = self.get_key_info(key=key)
            expires_str = key_info.get('info').get('expires')

            # Permanent token (no expiration) -> Active
            if not expires_str:
                active_tokens.append(key)
                continue

            try:
                # LiteLLM typically returns: "2024-11-24T23:19:11.131000Z"
                # Handle 'Z' manually for Python < 3.11 compatibility if needed
                if expires_str.endswith('Z'):
                    expires_str = expires_str[:-1] + '+00:00'

                # Parse ISO format
                expiry_date = datetime.fromisoformat(expires_str)

                # Ensure expiry_date is timezone-aware for comparison
                if expiry_date.tzinfo is None:
                    expiry_date = expiry_date.replace(tzinfo=timezone.utc)

                if expiry_date > now:
                    active_tokens.append(key)

            except (ValueError, TypeError):
                continue

        return {
            'success': True,
            'user_id': user_id,
            'count': len(active_tokens),
            'data': active_tokens
        }

