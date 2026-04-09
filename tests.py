"""
熵食源 - 测试文件
"""
import pytest
from app import app, db
from models import User, Food, Exercise

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()

def test_index_page(client):
    """测试首页"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'\u71c3\u98df\u6e90' in response.data or b'entropy' in response.data.lower()

def test_register(client):
    """测试注册功能"""
    response = client.post('/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'test123456'
    }, follow_redirects=True)
    assert response.status_code == 200

def test_login(client):
    """测试登录功能"""
    # 先注册
    client.post('/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'test123456'
    })
    
    # 再登录
    response = client.post('/login', data={
        'email': 'test@example.com',
        'password': 'test123456'
    }, follow_redirects=True)
    assert response.status_code == 200

def test_food_api(client):
    """测试食物API"""
    response = client.get('/api/foods?q=')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)

def test_calculate_bmi():
    """测试BMI计算"""
    with app.app_context():
        user = User(weight=70, height=175)
        bmi = user.get_bmi()
        assert 22 <= bmi <= 23

def test_calculate_bmr():
    """测试BMR计算"""
    with app.app_context():
        # 男性
        user_male = User(weight=70, height=175, gender='male', age=30)
        bmr_male = user_male.get_bmr()
        assert bmr_male > 1500
        
        # 女性
        user_female = User(weight=60, height=165, gender='female', age=25)
        bmr_female = user_female.get_bmr()
        assert bmr_female > 1200

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
