python3.13 -m pip install --break-system-packages -r requirements.txt
cp telelite.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable myapp.service
systemctl start myapp.service
systemctl status myapp.service