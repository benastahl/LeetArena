define = """
def say_hi(name):
    print(f"Hello, {name}")
    return "Did it!"
"""
exec(define)
ret = eval("say_hi('benjamin')")
print(ret)
