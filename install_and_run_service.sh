python3.13 -m pip install --break-system-packages -r requirements.txt
cp telelite.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable telelite.service
systemctl start telelite.service
systemctl status telelite.service