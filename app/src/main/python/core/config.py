import os
class AppConfig:
    def __init__(self):
        self.secret_key=os.environ.get("TPV_SECRET_KEY",os.urandom(24).hex())
        self.port=int(os.environ.get("TPV_PORT",5000))
        self.https=os.environ.get("TPV_HTTPS","0")=="1"
        self.demo_password=os.environ.get("TPV_DEMO_PASSWORD","CAMBIAME-EN-PRODUCCION")
    def validate(self):
        w=[]
        if not os.environ.get("TPV_SECRET_KEY"): w.append("TPV_SECRET_KEY no establecida")
        if self.demo_password=="CAMBIAME-EN-PRODUCCION": w.append("TPV_DEMO_PASSWORD sin cambiar")
        return w
config=AppConfig()
