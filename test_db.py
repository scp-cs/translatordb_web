from db import *

if __name__ == "__main__":
    print(Frontpage.select().get().user.id)