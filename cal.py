def calculate(a, op, b):
    if op == "*":
        return a * b
    elif op == "/":
        return a / b
    elif op == "+":
        return a + b
    elif op == "-":
        return a - b
    

while True:
    user_input = input("수식을 입력하세요")
    if user_input == "q":
        break
    parts = user_input.split()
    a = int(parts[0])
    op = parts[1]
    b = int(parts[2])
        
    result = calculate(a,op,b)
    print(result)
