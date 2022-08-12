def run_python_script():
    python_script = """
    #! -*- coding:utf-8 -*-
def test():
    print('hello world')
print(test())
    """
    exec(python_script, globals())


run_python_script()
