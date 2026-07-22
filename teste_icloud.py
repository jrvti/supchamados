from pyicloud import PyiCloudService

# Teste com senha específica
email = "tecnico@jrvti.com.br"
senha = "ogzg-guhs-jmwa-hjmg"  # nova senha do email tecnico

print(f"Testando login com: {email}")
print(f"Senha: {senha[:4]}...")

try:
    api = PyiCloudService(email, senha)
    print(f"✅ Login OK!")
    print(f"Requires 2FA: {api.requires_2fa}")
    
    if not api.requires_2fa:
        # Tenta acessar calendários
        calendars = api.calendar.get_calendars()
        print(f"✅ Calendários encontrados: {len(calendars)}")
        for cal in calendars:
            print(f"   - {cal.get('title')}")
except Exception as e:
    print(f"❌ Erro: {e}")