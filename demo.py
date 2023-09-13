class Data:
    pass


setattr(Data, "token", 1)
run_time = {"runtime": "${token}"}
value = getattr(Data, "token")
values = "${token}".replace("${{mark}}".replace("{mark}", var[0]), str(value))
