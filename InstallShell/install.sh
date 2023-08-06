# SSH
ssh nizai9a@140.250.51.124 -p 33322
qwe11111

# 防火墙
sudo ufw disable
sudo adduser [colin]
sudo usermod -aG sudo [colin]

# Snap
sudo apt install snapd
snap install btop

# 安装Mysql
sudo apt update
sudo apt install mysql-server
sudo mysql_secure_installation
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf

# 修改bind-address
bind-address = 0.0.0.0
mysqlx-bind-address = 0.0.0.0
sudo service mysql restart

# 创建用户
sudo mysql -u root -p
CREATE USER 'colin'@'%' IDENTIFIED BY '^Q}spft2L0bmX^+=X=v0'
GRANT ALL ON *.* TO 'colin'@'%'
FLUSH PRIVILEGES
EXIT

# 安装miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# 安装软件包
conda create -n PlaySpider python==3.10
conda activate PlaySpider
conda install -c conda-forge scrapy
pip install playwright mysql-connector-python -i https://pypi.tuna.tsinghua.edu.cn/simple
playwright install

#
sudo mkdir /home/nizai9a/PycharmProjects
sudo chmod -R 777 /home/nizai9a/PycharmProjects
