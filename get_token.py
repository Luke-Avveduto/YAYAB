def get_token():
    with open("discord-core/token.txt") as f:
        return f.readlines()[0]
