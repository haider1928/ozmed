from python_shell import PythonShell

def main():
    shell = PythonShell()

    print("OZMED Python Shell (type 'reset' or 'exit')")

    while True:
        print("\nEnter code (single line). Commands: reset / exit")

        line = input(">>> ")

        if line.strip().lower() == "exit":
            break

        if line.strip().lower() == "reset":
            print(shell.reset()[0])
            continue

        # run single line wrapped as list
        outputs = shell.run([line])

        for o in outputs:
            print(o)


if __name__ == "__main__":
    main()