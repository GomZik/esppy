def target(a):
    print('Hello from process')
    print(a)

if __name__ == '__main__':
    pid = spawn('test', 'target', 'test')
