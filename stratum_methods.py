def reconnect():
    output = {
        "id": None,
        "method": "client.reconnect",
        "params": []}
    return output


def authorize(user, passw):
    output = {"params": [user, passw],
              "id": 2,
              "method": "mining.authorize"}
    return output
