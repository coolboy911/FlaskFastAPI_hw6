import databases
import sqlalchemy
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List
import uvicorn

app = FastAPI()
DATABASE_URL = 'sqlite:///my_database.db'
database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

# creating tables for database
users = sqlalchemy.Table(
    'users',
    metadata,
    sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column('name', sqlalchemy.String(32)),
    sqlalchemy.Column('second_name', sqlalchemy.String(60)),
    sqlalchemy.Column('email', sqlalchemy.String(128)),
    sqlalchemy.Column('password', sqlalchemy.String(50)),
)

products = sqlalchemy.Table(
    'products',
    metadata,
    sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column('name', sqlalchemy.String(128)),
    sqlalchemy.Column('description', sqlalchemy.Text())
)

orders = sqlalchemy.Table(
    'orders',
    metadata,
    sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column('user_id', sqlalchemy.Integer, sqlalchemy.ForeignKey(users.c.id)),
    sqlalchemy.Column('product_id', sqlalchemy.Integer, sqlalchemy.ForeignKey(products.c.id)),
    sqlalchemy.Column('date', sqlalchemy.String(10), default='2020-01-01'),
    sqlalchemy.Column('description', sqlalchemy.Text()),
    sqlalchemy.Column('price', sqlalchemy.Float()),
)

engine = sqlalchemy.create_engine(
    DATABASE_URL, connect_args={'check_same_thread': False}
)
metadata.create_all(engine)


# creating pydantic models
class User(BaseModel):
    id: int
    name: str = Field(max_length=32)
    second_name: str = Field(max_length=60)
    email: str = Field(max_length=128)
    password: str = Field(max_length=50)


class UserIn(BaseModel):
    name: str = Field(max_length=32)
    second_name: str = Field(max_length=60)
    email: str = Field(max_length=128)
    password: str = Field(max_length=50)


class Product(BaseModel):
    id: int
    name: str = Field(max_length=128)
    description: str = Field(default='')


class ProductIn(BaseModel):
    name: str = Field(max_length=128)
    description: str = Field(default='')


class Order(BaseModel):
    id: int
    user_id: int
    product_id: int
    date: str
    description: str
    price: float


class OrderIn(BaseModel):
    user_id: int
    product_id: int
    date: str
    description: str
    price: float


# main site logic
JSON_RESPONSE_404_DB = JSONResponse(content={'message': 'content not found in database'}, status_code=404)


# users
@app.get('/users/', response_model=List[User])
async def read_users():
    query = users.select()
    return await database.fetch_all(query)


@app.post('/users/', response_model=User)
async def create_user(user: UserIn):
    query = users.insert().values(**user.dict())
    last_record_id = await database.execute(query)
    return {**user.dict(), 'id': last_record_id}


@app.get('/users/{user_id}', response_model=User)
async def read_user(user_id: int):
    query = users.select().where(users.c.id == user_id)
    result = await database.fetch_one(query)
    if result:
        return result
    else:
        return JSON_RESPONSE_404_DB


@app.put('/users/{user_id}', response_model=User)
async def update_user(user_id: int, new_user: UserIn):
    query = users.update().where(users.c.id == user_id).values(**new_user.dict())
    result = await database.execute(query)
    if result:
        return {**new_user.dict(), 'id': user_id}
    else:
        return JSON_RESPONSE_404_DB


@app.delete('/users/{user_id}')
async def delete_user(user_id: int):
    query = users.delete().where(users.c.id == user_id)
    result = await database.execute(query)
    if result:
        return {'message': f'user with user_id:{user_id} was deleted'}
    else:
        return JSON_RESPONSE_404_DB


# products
@app.get('/products/', response_model=List[Product])
async def read_products():
    query = products.select()
    return await database.fetch_all(query)


@app.post('/products/', response_model=Product)
async def create_product(product: ProductIn):
    query = products.insert().values(**product.dict())
    last_record_id = await database.execute(query)
    return {**product.dict(), 'id': last_record_id}


@app.get('/products/{product_id}', response_model=Product)
async def read_product(product_id: int):
    query = products.select().where(products.c.id == product_id)
    result = await database.fetch_one(query)
    if result:
        return result
    else:
        return JSON_RESPONSE_404_DB


@app.put('/products/{product_id}', response_model=Product)
async def update_product(product_id: int, new_product: UserIn):
    query = products.update().where(products.c.id == product_id).values(**new_product.dict())
    result = database.execute(query)
    if result:
        return {**new_product.dict(), 'id': product_id}
    else:
        return JSON_RESPONSE_404_DB


@app.delete('/products/{product_id}')
async def delete_product(product_id: int):
    query = products.delete().where(products.c.id == product_id)
    result = await database.execute(query)
    if result:
        return {'message': 'product deleted'}
    else:
        return JSON_RESPONSE_404_DB


# orders
@app.get('/orders/', response_model=List[Order])
async def read_orders():
    query = orders.select()
    return await database.fetch_all(query)


@app.post('/orders/', response_model=Order)
async def create_order(order: OrderIn):
    # fetching user
    result = await database.fetch_one(users.select().where(users.c.id == order.user_id))
    if not result:
        return JSON_RESPONSE_404_DB
    # fetching product
    result = await database.fetch_one(products.select().where(products.c.id == order.product_id))
    if not result:
        return JSON_RESPONSE_404_DB
    query = orders.insert().values(**order.dict())
    last_record_id = await database.execute(query)
    return {**order.dict(), 'id': last_record_id}


@app.get('/orders/{order_id}', response_model=Order)
async def read_order(order_id: int):
    query = orders.select().where(orders.c.id == order_id)
    result = await database.fetch_one(query)
    if result:
        return result
    else:
        return JSON_RESPONSE_404_DB


@app.put('/orders/{order_id}', response_model=Order)
async def update_order(order_id: int, new_order: OrderIn):
    # fetching user
    result = await database.fetch_one(users.select().where(users.c.id == new_order.user_id))
    if not result:
        return JSON_RESPONSE_404_DB
    # fetching product
    result = await database.fetch_one(products.select().where(products.c.id == new_order.product_id))
    if not result:
        return JSON_RESPONSE_404_DB

    query = orders.update().where(orders.c.id == order_id).values(**new_order.dict())
    result = await database.execute(query)
    if result:
        return {**new_order.dict(), 'id': order_id}
    else:
        return JSON_RESPONSE_404_DB


@app.delete('/orders/{order_id}')
async def delete_user(order_id: int):
    query = orders.delete().where(orders.c.id == order_id)
    await database.execute(query)
    return {'message': 'order deleted'}


if __name__ == '__main__':
    uvicorn.run('task001:app', host='127.0.0.1', port=8000)
