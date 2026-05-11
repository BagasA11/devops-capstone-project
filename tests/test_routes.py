"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"


######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # ADD YOUR TEST CASES HERE ...
    def test_list_all(self):
        """It should return list of account dictionary if exists or empty list [] otherwise"""
        # check empty list
        empty_response = self.client.get('/accounts')
        self.assertNotEqual(empty_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(empty_response.status_code, status.HTTP_200_OK)
        empty_data = empty_response.get_json()
        self.assertEqual(empty_data, [])

        # fill and check 
        # if create batch of 5, then returned data must be 5
        accounts = self._create_accounts(5)
        response = self.client.get('/accounts')
        dataset = response.get_json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(dataset), len(accounts))

        # ensure all list item are dictionary instance
        for data in dataset:
            self.assertIsInstance(data, dict)
    
    def test_read_an_account(self):
        """It should read an single account"""
        account = self._create_accounts(1)[0]
        response = self.client.get(f'{BASE_URL}/{account.id}', content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data['name'], account.name)

    def test_not_found_account(self):
        """should return 404 code"""
        response = self.client.get(f'{BASE_URL}/1', content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_update_an_account(self):
        """It should return a valid user account dictionary"""
        test_account = AccountFactory()
        response = self.client.post(f'{BASE_URL}', json=test_account.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        new_account = response.get_json()
        new_account['name'] = 'Luthfi'
        response = self.client.put(f"{BASE_URL}/{new_account['id']}", json=new_account)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_account = response.get_json()
        self.assertEqual(updated_account['name'], new_account['name'])

    def test_update_not_found_id(self):
        """It should return 404 not found"""
        account = AccountFactory()
        response = self.client.put(f'{BASE_URL}/1', json=account.serialize())
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_update_with_empty_data(self):
        """It should return 400 Bad Request"""
        response = self.client.put(f'{BASE_URL}/1')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_an_account(self):
        """It should deleted account and return 204 no content"""
        test_account = self._create_accounts(1)[0]
        id = test_account.id 
        response = self.client.delete(f"{BASE_URL}/{id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        empty = self.client.get(f'{BASE_URL}')
        self.assertEqual(empty.status_code, status.HTTP_200_OK)
        self.assertEqual(empty.get_json(), [])
            
    def test_delete_not_found(self):
        notfound = self.client.delete(f'{BASE_URL}/1')
        self.assertEqual(notfound.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_method_not_allowed_handler(self):
        """It should  return HTTP_405_METHOD_NOT_ALLOWED"""
        response = self.client.delete(f"{BASE_URL}")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)