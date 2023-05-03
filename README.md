# dist-sys-project

## Instructions:
### Client
The client doesn't require any dependencies and can be started by entering the client directory and running `python main.py <host> <port>`. If the host and port are left blank, it defaults to `localhost:5000` which the server will also default to if running locally.

### Server
The server requires mongoengine and MongoDB to run. To install mongoengine simply run `pip install mongoengine`. MongoDB is slightly more complicated and the installation instructions will vary based on your operating system. Follow the relevant instructions for the *Community Edition* here: https://www.mongodb.com/docs/manual/installation/

The server is started by entering the server directory and running `python main.py <port>` where the port defaults to 5000.

### Gameplay
Once the server and client are running, you can create a new user or login by following the prompt given by the client. Available commands are displayed by typing `help`. In game, features, items, and enemies that are interactable will be surrounded by square brackets indicating the keyword you can call using the commands available. For example, if you looked at the room and it said "`There is a [torch] on the wall`", you could try to pick it up with `grab torch` or interact with it via `use torch`. Good luck!

<details>
<summary>Gameplay Walkthrough (only check if you're stuck!!)</summary>

1. `grab small-key`
2. `use door`
3. `grab crowbar`
4. `use door`
5. `use trapdoor`
6. `use trapdoor`
7. `use iron-door`
8. `attack skeleton` (repeat until dead)
9. `grab dungeon-key`
10. `use gold-door`
11. `use gold-door`
12. `look tablet`


</details>
