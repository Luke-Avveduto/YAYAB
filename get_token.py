def get_token():
    with open("token.txt") as f:
        return f.readlines()[0]
