import asyncio
from urllib.parse import parse_qs
from http.cookies import SimpleCookie

class HTTPServer:
    MAX_REQUEST_SIZE = 10 * 1024  # 最大允许请求大小（10KB）
    MAX_HEADER_SIZE = 10 * 1024  # 最大允许头部大小（10KB）
    MAX_POST_SIZE = 5000 * 1024  # 最大允许POST大小（5MB）

    def __init__(self, host, port):
        self.host = host
        self.port = port

    async def handle_request(self, reader, writer):
        request_data = await reader.read(self.MAX_REQUEST_SIZE)
        request = request_data.decode()

        try:
            method, path, request_lines = self.parse_request(request)

            # 解析GET参数
            get_params = {}
            if '?' in path:
                path, query_string = path.split('?', 1)
                get_params = parse_qs(query_string)

            # 解析Cookie
            cookies = {}
            for line in request_lines:
                if line.startswith('Cookie:'):
                    cookie_header = line.split(':', 1)[1].strip()
                    cookie = SimpleCookie()
                    cookie.load(cookie_header)
                    cookies = {key: cookie[key].value for key in cookie}
                    break

            if method == 'GET':
                # 处理GET请求
                response_headers, response_content = self.build_response(path, get_params, {}, cookies)

            elif method == 'POST':
                # 处理POST请求
                content_length = 0
                for line in request_lines:
                    if line.startswith('Content-Length:'):
                        content_length = int(line.split(':')[1])
                        break

                if content_length > self.MAX_POST_SIZE:
                    raise ValueError('POST请求太大')

                post_data = request.split('\r\n\r\n', 1)[1][:content_length]
                post_params = parse_qs(post_data)

                response_headers, response_content = self.build_response(path, get_params, post_params, cookies)

            else:
                raise ValueError('不支持的HTTP方法')

            response = '\r\n'.join(response_headers) + '\r\n\r\n' + response_content
            writer.write(response.encode())
            await writer.drain()

        except ValueError as e:
            response_headers, response_content = self.build_error_response(413, str(e))
            response = '\r\n'.join(response_headers) + '\r\n\r\n' + response_content
            writer.write(response.encode())
            await writer.drain()

        except Exception as e:
            response_headers, response_content = self.build_error_response(500, '服务器内部错误')
            response = '\r\n'.join(response_headers) + '\r\n\r\n' + response_content
            writer.write(response.encode())
            await writer.drain()

        writer.close()

    def parse_request(self, request):
        request_lines = request.split('\n')
        if len(request_lines) > 0:
            request_line = request_lines[0].strip()
            method, path, _ = request_line.split(' ')

            request_headers_size = sum(len(line) + 2 for line in request_lines)
            if request_headers_size > self.MAX_HEADER_SIZE:
                raise ValueError('请求头太大')

            return method, path, request_lines

        raise ValueError('无效的请求')

    def build_response(self, path, get_params, post_params, cookies):
        response_content = f"<h1>Hello, World!</h1><p>请求路径：{path}</p><p>GET参数：{get_params}</p><p>POST参数：{post_params}</p><p>Cookie：{cookies}</p>"
        response_headers = [
            'HTTP/1.1 200 OK',
            'Content-Type: text/html; charset=utf-8',
            'Content-Length: ' + str(len(response_content)),
            'Connection: close',
        ]

        cookie = SimpleCookie()
        cookie['cookie_name'] = 'cookie_value'
        cookie['cookie_name']['path'] = '/'
        cookie['cookie_name']['max-age'] = 3600
        response_headers.append(cookie.output(header='Set-Cookie'))

        return response_headers, response_content

    def build_error_response(self, status_code, status_message):
        response_content = f"<h1>{status_code} {status_message}</h1>"
        response_headers = [
            f'HTTP/1.1 {status_code} {status_message}',
            'Content-Type: text/html; charset=utf-8',
            'Content-Length: ' + str(len(response_content)),
            'Connection: close',
        ]
        return response_headers, response_content

    async def run_server(self):
        server = await asyncio.start_server(self.handle_request, self.host, self.port)

        addr = server.sockets[0].getsockname()
        print(f'服务器正在运行，访问地址：http://{addr[0]}:{addr[1]}')

        async with server:
            await server.serve_forever()

if __name__ == '__main__':
    server = HTTPServer('127.0.0.1', 8008)
    asyncio.run(server.run_server())
