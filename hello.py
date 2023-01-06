import os,time
os.system('''apk add g++ jpeg-dev zlib-dev libffi-dev libjpeg make''')
os.system('pip install --upgrade pip')
os.system("pip3 install -r requirements2.txt")
os.system("python3 app2.py")
