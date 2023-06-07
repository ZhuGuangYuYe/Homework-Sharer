import asyncio
from urllib.parse import parse_qs

class HTTPServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    async def handle_request(self, reader, writer):
        request_data = await reader.read(1024)
        request = request_data.decode()
        # 获取请求行
        request_lines = request.split('\n')
        if len(request_lines) > 0:
            request_line = request_lines[0].strip()
            # 获取请求方法和路径
            method, path, _ = request_line.split(' ')

            # 解析GET参数
            get_params = {}
            if '?' in path:
                path, query_string = path.split('?', 1)
                get_params = parse_qs(query_string)

            # 解析POST参数
            content_length = 0
            for line in request_lines:
                if line.startswith('Content-Length:'):
                    content_length = int(line.split(':')[1])
                    break
            post_data = request.split('\r\n\r\n', 1)[1][:content_length]
            post_params = parse_qs(post_data)

            # 处理请求
            # 构建响应内容
            response_content = f"<h1>Hello, World!</h1><p>Requested path: {path}</p><p>GET parameters: {get_params}</p><p>POST parameters: {post_params}</p>"
            # 构建响应头
            response_headers = [
                'HTTP/1.1 200 OK',
                'Content-Type: text/html; charset=utf-8',
                'Content-Length: ' + str(len(response_content)),
                'Connection: close',
                '\r\n'
            ]
            # 发送响应
            response = '\r\n'.join(response_headers) + response_content
            writer.write(response.encode())
            await writer.drain()

        writer.close()

    async def run_server(self):
        server = await asyncio.start_server(
            self.handle_request, self.host, self.port)

        addr = server.sockets[0].getsockname()
        print(f'Server is running at http://{addr[0]}:{addr[1]}')

        async with server:
            await server.serve_forever()

if __name__ == '__main__':
    server = HTTPServer('127.0.0.1', 8008)
    asyncio.run(server.run_server())
