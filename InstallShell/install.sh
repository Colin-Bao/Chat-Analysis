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
mysql+mysqldb://colin:^Q}spft2L0bmX^+=X=v0@140.250.51.124:3306]/airflow_db
EXIT

# 安装miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# 安装软件包
conda create -n PlaySpider python==3.10
conda activate PlaySpider
conda install -c conda-forge scrapy numpy pandas sqlalchemy
pip install playwright mysql-connector-python -i https://pypi.tuna.tsinghua.edu.cn/simple
playwright install

#
sudo mkdir /home/nizai9a/PycharmProjects
sudo chmod -R 777 /home/nizai9a/PycharmProjects

# CPU性能
#sudo apt install cpufrequtils
#for i in $(seq 0 $(($(nproc) - 1)));do sudo cpufreq-set -c $i -g performance;
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

nohup airflow webserver -p 8000 >/home/webserver.log 2>&1 &
nohup airflow scheduler >/home/scheduler.log 2>&1 &

ps aux | grep "airflow scheduler"
ps aux | grep "airflow webserver"


pkill -9 -f "airflow scheduler"
pkill -9 -f "airflow webserver"
lsof -i :8793
lsof -i :8000



kill -9 1089951


#
ln -s /home/nizai9a/PycharmProjects/Chat-Analysis/ScrapySpider/playwright_spider/duopei_dags /home/nizai9a/airflow/dags

pip install mysql-connector-python

# 运行airflow
conda activate PlaySpider
airflow db init
airflow users  create --role Admin --username admin --email admin --firstname admin --lastname admin --password admin
/home/nizai9a/miniconda3/envs/PlaySpider/bin/airflow scheduler
/home/nizai9a/miniconda3/envs/PlaySpider/bin/airflow webserver -p 8000

sudo nano /etc/systemd/system/airflow-webserver.service
sudo systemctl start airflow-webserver
sudo systemctl start airflow-scheduler
sudo systemctl enable airflow-webserver
sudo systemctl disable airflow-webserver airflow-scheduler
sudo systemctl status airflow-webserver
journalctl -u airflow-webserver.service -f
journalctl -u airflow-scheduler.service -f
sudo systemctl status airflow-scheduler
sudo systemctl restart airflow-webserver airflow-scheduler

# 重装
sudo systemctl stop airflow-webserver airflow-scheduler
sudo systemctl restart mysql
conda activate PlaySpider
airflow db upgrade
airflow db init
airflow users  create --role Admin --username colin --email colin --firstname colin --lastname colin --password colin
sudo systemctl restart airflow-webserver airflow-scheduler
airflow scheduler
airflow webserver

# 使用代理
airflow webserver -D
airflow scheduler -D
airflow celery worker -D