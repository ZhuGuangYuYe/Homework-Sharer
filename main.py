import asyncio
from urllib.parse import parse_qs
from http.cookies import SimpleCookie

class HTTPServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    async def handle_request(self, reader, writer):
        request_data = await reader.read(1024)
        request = request_data.decode()
        try:
            request_lines = request.split('\n')
            # 获取请求行
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

                # 解析Cookie
                cookies = {}
                for line in request_lines:
                    if line.startswith('Cookie:'):
                        cookie_header = line.split(':', 1)[1].strip()
                        cookie = SimpleCookie()
                        cookie.load(cookie_header)
                        cookies = {key: cookie[key].value for key in cookie}
                        break

                # 处理请求
                response_headers, response_content = self.build_response(path, get_params, post_params, cookies)

                # 发送响应
                response = '\r\n'.join(response_headers) + response_content
                writer.write(response.encode())
                await writer.drain()

        except ValueError:
            response_headers, response_content = self.build_error_response(400, 'Bad Request')
            response = '\r\n'.join(response_headers) + response_content
            writer.write(response.encode())
            await writer.drain()

        except Exception as e:
            response_headers, response_content = self.build_error_response(500, 'Internal Server Error')
            response = '\r\n'.join(response_headers) + response_content
            writer.write(response.encode())
            await writer.drain()

        writer.close()

    def build_response(self, path, get_params, post_params, cookies):
        # 构建响应内容
        response_content = f"<h1>Hello, World!</h1><p>Requested path: {path}</p><p>GET parameters: {get_params}</p><p>POST parameters: {post_params}</p><p>Cookies: {cookies}</p>"
        # 构建响应头
        response_headers = [
            'HTTP/1.1 200 OK',
            'Content-Type: text/html; charset=utf-8',
            'Content-Length: ' + str(len(response_content)),
            'Connection: close',
            '\r\n'
        ]

        # 设置需要设置的Cookie
        cookie = SimpleCookie()
        cookie['cookie_name'] = 'cookie_value'
        cookie['cookie_name']['path'] = '/'
        cookie['cookie_name']['max-age'] = 3600  # 设置Cookie的过期时间，单位为秒

        # 将Cookie添加到响应头中
        response_headers.append(cookie.output(header='Set-Cookie'))

        return response_headers, response_content

    def build_error_response(self, status_code, status_message):
        response_content = f"<h1>{status_code} {status_message}</h1>"
        response_headers = [
            f'HTTP/1.1 {status_code} {status_message}',
            'Content-Type: text/html; charset=utf-8',
            'Content-Length: ' + str(len(response_content)),
            'Connection: close',
            '\r\n'
        ]
        return response_headers, response_content

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
