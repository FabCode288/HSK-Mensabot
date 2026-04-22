After successfull boot run the following commands:

sudo apt update
sudo apt upgrade -y
sudo apt install openssh-server -y
sudo systemctl enable ssh
sudo systemctl start ssh

sudo reboot

Then create the workspace and copy the folders src and setup:
cd
mkdir ros2_mensabot_ws

clone the Repo here to have this structure:
student@Mensabot:~/ros2_mensabot_ws/ README.md  scripts  src

Then run the pi_setup.sh:

cd
bash ros2_mensabot_ws/scripts/pi_setup.sh
