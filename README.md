## 商城微服务（后端实现）

### 上层服务使用`golang + gin`提供`http`接口
### 底层服务使用`python`提供数据库等底层操作，暴露`grpc`接口

### 技术栈
- 数据库：`MySQL`
- 缓存：`Redis`
- 服务器注册和发现：`Consul`
    - [consul](https://github.com/hashicorp/consul)
    - docker run  --restart=always --name consul -d -p 8500:8500 -p 8300:8300 -p 8301:8301 -p 8302:8302 -p 8600:8600/udp consul consul agent  -dev -client="0.0.0.0"
    - http://127.0.0.1:8500/
- 配置中心：`nacos`
    - [nacos](https://github.com/alibaba/nacos)
    - docker run --name nacos-standalone -e MODE=standalone -e JVM_XMS=1024m -e JVM_XMX=1024m -e JVM_XMN=256m -p 8848:8848 -d nacos/nacos-server:latest
    - http://127.0.0.1:8848/nacos
- 消息队列：`rocketmq`
    - [rocketmq](https://github.com/apache/rocketmq)
    - http://127.0.0.1:8280/
- 链路追踪：`jaeger`
    - [jaeger](https://github.com/jaegertracing/jaeger)
    - docker run -d --name jaeger -p6831:6831/udp -p16686:16686 jaegertracing/all-in-one:latest
    - http://127.0.0.1:16686/
- api网关：`kong`
    - [kong](https://github.com/Kong/kong)
        1. 依赖postgresql(docker run -d --name kong-db -e 5432:5432 -e "POSTGRES_USER=kong" -e "POSTGRES_DB=kong" -e "POSTGRES_PASSWORD=kong" postgres:12)
        2. sudo yum -y install https://bintray.com/kong/kong-rpm/download_file?file_path=centos/7/kong-2.1.0.e17.amd64.rpm
        3. 配置
            - cp /etc/kong/kong.conf.default /etc/kong/kong.conf
            - vim /etc/kong/kong.conf
            ```shell
            # 修改
            database = 
            pg_host = 
            pg_port = 
            pg_timeout = 

            pg_user = 
            pg_password = 
            pg_database = 

            dns_resolver = 127.0.0.1:8600  # consul的dns端口。默认8600
            admin_listen =  # 这一行的127.0.0.1修改为0.0.0.0
            proxy_listen = # 打开
            ```
        4. kong migrations bootstrap up -c /etc/kong/kong.conf  # 初始化生成数据库
        5. kong start -c /etc/kong/kong.conf 
    - [konga](https://github.com/pantsel/konga) # kong ui
        - docker run -d -p 1337:1337 --name konga pantsel/konga 127.0.0.1:1337
