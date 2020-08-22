import pymongo

def update_data(collection, id, new_values):  # update data in mongodb collection
    collection.update_one({'id': id}, {'$set': new_values})


def insert_data(collection, data):  # for data inserting to mongodb collection
    return collection.insert_one(data).inserted_id


def find_data(collection, data, multiple=False):  # serching data in mongodb collection
    if multiple:  # if you didn't set multiple var as True, it'll be False at default
        results = collection.find(data)
        return [r for r in results]
    else:
        return collection.find_one(data)


def delete_data(collection, id):
    collection.deleteOne({"id": int(id}))
    return 0