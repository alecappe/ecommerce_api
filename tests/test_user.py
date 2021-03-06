from http.client import CREATED, NO_CONTENT, NOT_FOUND, BAD_REQUEST, UNAUTHORIZED
import json
import uuid
from views.user import crypt_password
from peewee import SqliteDatabase
from models import User
from app import app
import base64


class Testuser:
    @classmethod
    def setup_class(cls):
        User._meta.database = SqliteDatabase(':memory:')
        User.create_table()
        cls.app = app.test_client()

    def setup_method(self):
        User.delete().execute()

    def open_with_auth(self, url, method, email, password, data):
        return self.app.open(
            url, method=method, headers={'Authorization': 'Basic ' + base64.b64encode(
                bytes(email + ":" + password, 'ascii')).decode('ascii')}, data=data)

    def test_post__success_empty_db(self):
        data = {
            'first_name': 'Alessandro',
            'last_name': 'Cappellini',
            'email': 'emailprova@pippo.it',
            'password': '1234567'
        }
        resp = self.app.post('/users/', data=data)
        query = User.select()
        user_from_db = User.get()
        expected_data = {
            'first_name': user_from_db.first_name,
            'last_name': user_from_db.last_name,
            'email': user_from_db.email,
            'password': data['password']
        }
        assert expected_data == data
        assert resp.status_code == CREATED
        assert len(query) == 1
        assert query.get().json() == json.loads(resp.data.decode())

    def test_post__success(self):
        data = {
            'first_name': 'Anna',
            'last_name': 'Markis',
            'email': 'anna@markis.com',
            'password': '1234567'
        }

        id_user_created = uuid.uuid4()

        User.create(
            uuid=id_user_created,
            first_name='Giovanni',
            last_name='Mariani',
            email='giovanni@mariani.com',
            password='1234'
        )

        resp = self.app.post('/users/', data=data)
        query = User.select().where(User.uuid != id_user_created)
        assert resp.status_code == CREATED
        assert query.get().json() == json.loads(resp.data.decode())

    def test_post__empty_field(self):
        data = {
            'first_name': '',
            'last_name': 'Alessandro',
            'email': 'alessandro@hotmail.com',
            'password': '1234'
        }

        resp = self.app.post('/users/', data=data)
        assert resp.status_code == BAD_REQUEST
        assert len(User.select()) == 0

    def test_post__field_not_exists(self):
        data = {
            'last_name': 'Pippo',
            'email': 'mark@pippo.it',
            'password': '123456'
        }

        resp = self.app.post('/users/', data=data)
        assert resp.status_code == BAD_REQUEST
        assert len(User.select()) == 0

    def test_put__success(self):
        user = User.create(
            uuid=uuid.uuid4(),
            first_name='Giovanni',
            last_name='Mariani',
            email='giovanni@mariani.com',
            password=crypt_password('1234567')
        )

        data = {
            'first_name': 'anna',
            'last_name': 'Marini',
            'email': 'giovanni@mariani.com',
            'password': '1234567'
        }

        resp = self.open_with_auth(
            '/users/{}'.format(user.uuid), 'put', user.email, '1234567', data=data)
        query = User.select()
        user_from_db = query.get()
        expected_data = {
            'first_name': user_from_db.first_name,
            'last_name': user_from_db.last_name,
            'email': user_from_db.email,
            'password': data['password']
        }

        assert expected_data == data
        assert resp.status_code == CREATED
        assert query.get().json() == json.loads(resp.data.decode())

    def test_put__modify_one_field(self):
        user = User.create(
            uuid=uuid.uuid4(),
            first_name='Giovanni',
            last_name='Mariani',
            email='giovanni@mariani.com',
            password=crypt_password('1234567')
        )

        data = {
            'first_name': 'Anna',
        }

        resp = self.open_with_auth(
            '/users/{}'.format(user.uuid), 'put', user.email, '1234567', data=data)
        assert resp.status_code == BAD_REQUEST

    def test_put__empty_fields(self):
        user = User.create(
            uuid=uuid.uuid4(),
            first_name='Giovanni',
            last_name='Mariani',
            email='giovanni@mariani.com',
            password=crypt_password('1234567')
        )

        data = {
            'first_name': '',
            'last_name': '',
            'email': '',
            'password': ''
        }

        resp = self.open_with_auth(
            '/users/{}'.format(user.uuid), 'put', user.email, '1234567', data=data)
        assert resp.status_code == BAD_REQUEST

    def test_put__user_unauthorized(self):
        user = User.create(
            uuid=uuid.uuid4(),
            first_name='Giovanni',
            last_name='Mariani',
            email='giovanni@mariani.com',
            password=crypt_password('1234567')
        )

        data = {
            'first_name': 'Giovanni',
            'last_name': 'Pippo',
            'email': 'giovanni@mariani.com',
            'password': '1234567'
        }

        resp = self.open_with_auth(
            '/users/{}'.format(user.uuid), 'put', user.email, '1234568', data=data)
        query = User.select().where(User.last_name == user.last_name)
        assert len(query) == 1
        assert resp.status_code == UNAUTHORIZED

    def test_put__user_unauthorized_for_modify_another_user(self):
        user = User.create(
            uuid=uuid.uuid4(),
            first_name='Maria',
            last_name='Rossi',
            email='maria@rossi.com',
            password=crypt_password('1234567')
        )
        user2 = User.create(
            uuid=uuid.uuid4(),
            first_name='Alessandro',
            last_name='Cappellini',
            email='abc@abc.com',
            password=crypt_password('1234567')
        )

        data = {
            'first_name': 'Anna',
            'last_name': 'Rossi',
            'email': 'maria@rossi.com',
            'password': '1234567'
        }

        resp = self.open_with_auth(
            '/users/{}'.format(user.uuid), 'put', user2.email, '1234567', data=data)
        assert resp.status_code == UNAUTHORIZED

    def test_delete_user__success(self):
        user = User.create(
            uuid=uuid.uuid4(),
            first_name='Alessandro',
            last_name='Cappellini',
            email='prova@pippo.com',
            password=crypt_password('1234567')
            )
        user2 = User.create(
            uuid=uuid.uuid4(),
            first_name='Jonh',
            last_name='Smith',
            email='jonh@smith.com',
            password=crypt_password('1234567')
            )

        resp = self.open_with_auth(
            '/users/{}'.format(user.uuid), 'delete', user.email, '1234567', data='')
        all_users = User.select()
        user_from_db = all_users.get()
        assert resp.status_code == NO_CONTENT
        assert len(all_users) == 1
        assert user_from_db.uuid == user2.uuid

    def test_delete__userid_not_exist(self):
        User.create(
            uuid=uuid.uuid4(),
            first_name='Alessandro',
            last_name='Rossi',
            email='a@b.it',
            password='ciaociao'
        )
        resp = self.open_with_auth(
            '/users/{}'.format(uuid.uuid4), 'delete', 'ciao@libero.it', '1234567', data='')
        assert resp.status_code == NOT_FOUND
        assert len(User.select()) == 1

    def test_delete_user__unauthorized_for_delete_another_user(self):
        user = User.create(
            uuid=uuid.uuid4(),
            first_name='Maria',
            last_name='Rossi',
            email='maria@rossi.com',
            password=crypt_password('1234567')
        )
        user2 = User.create(
            uuid=uuid.uuid4(),
            first_name='Alessandro',
            last_name='Cappellini',
            email='abc@abc.com',
            password=crypt_password('1234567')
        )

        resp = self.open_with_auth(
            '/users/{}'.format(user.uuid), 'delete', user2.email, '1234567', data='')
        assert resp.status_code == UNAUTHORIZED
