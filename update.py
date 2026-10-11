import os

if os.path.exists("log.txt"):
    with open("log.txt", "r+") as f:
        f.truncate(0)

print("update.py: skipping git update (Heroku mode)")
