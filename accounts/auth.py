from accounts.models import User
from django.contrib.auth.hashers import make_password,check_password


class Authentication:
  
  def signin(self, email: str, password: str) -> User | bool:
    try:
      user = User.objects.get(email=email)
      if check_password(password, user.password):
        return user
      else:
        return False
    except User.DoesNotExist:
      return False

  def signup(self, email: str, password: str, name: str) -> User | bool:
    
    if User.objects.filter(email=email).exists():
      raise False
    
    user = User(
      email=email,
      name=name,
      password=make_password(password)
    )
    
    user.save()
    
    return user