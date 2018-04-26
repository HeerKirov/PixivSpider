# PixivSpider
一个简单的Pixiv爬虫。
## 环境与包依赖
* Python 3.6.1
* beautifulsoup4==4.6.0
* requests==2.18.4
## 功能
* 根据Pixiv ID批量抓取图片。
* 根据画师Member ID批量抓取图片。
* 自定义下载位置和路径方案。
## 使用方式
为了使用脚本，应当配置一个conf.json文件。
调用`$ python app.py conf.json`来启用这个配置。
配置应当包括以下内容：
```
{
    account: {
        username: <string> 你用来模拟登录的Pixiv 用户名。
        password: <string> 此账户的密码。
    }
    proxy: <bool> 是否启用随机代理。默认是启用的。
    log: <filepath> 日志的输出文件位置。默认值为null，这会将日志打印到屏幕。
    content: [
        {...} 需要下载的配置块。可以列出多个配置块。
    ]
}
```
配置块应当包裹在一个JSON Object内。目前的配置块有2种可用的写法：
1. 基于Pixiv ID进行批量下载。
```
{
    pid: <array|string|int> 要批量下载的Pixiv ID或其列表。
                            语法比较宽松。可以写 
                                pid: 12345678
                                pid: "12345678"
                                pid: [12345678, 23456789]
                            这样的语法。
                            此外，还可以写"12345678-12345690"这样的语法，指定一连串的Pixiv ID。
}
```
2. 基于画师的Member ID进行批量下载。
```
{
    uid: <array|string|int> 要批量下载的画师的ID或其列表。
                            语法比较宽松。可以写
                                uid: 12345678
                                uid: "12345678"
                                uid: [12345678, 23456789]
                            这样的语法。
                            此外，还可以写"12345678[10]"或"12345678[2-20]"这样的语法，指定下载该画师的哪些作品。
}
```
除了上面的特有配置之外，还有所有的配置块都可以写的通用配置。
```
{
    enabled: <bool> 可用。默认是可用的，可以临时设为不可用，起到注释的作用。
    replace: <bool> 覆盖。重复下载同名文件时，覆盖之前的文件。默认是不覆盖的。
    save: <file_expression> 单文件存储路径。Pixiv ID下只有一张画时使用这个路径。必须指定。
    multi_save: <file_expression> 多文件存储路径。有多张画时使用此路径。
                                  可以不指定，但是会使下载器只下载第1张，并采用save路径。
}
```
有关save路径的写法，规则如下：
* 可以使用绝对路径或相对路径。
* 路径分隔符使用`/`。
* 使用`{prop}`的语法，在路径中插入关键值。可以插入的关键值包括：
    1. `{title}` 作品标题
    2. `{pid}` Pixiv ID
    3. `{user}` 作者用户名
    4. `{uid}` 作者的Member ID。
    5. `{index}` 仅multi_save中可用，表示画的索引值。
* 文件路径不应当带扩展名，扩展名会由下载器自动补全。
## 配置文件示例
```json
{
  "account": {
    "username": "username@gmail.com",
    "password": "******"
  },
  "proxy": true,
  "log": null,
  "content": [
    {
      "pid": [
        68126580,
        68079191,
        "68145900-6815905"
      ],
      "replace": false,
      "save": "save/{pid}",
      "multi_save": "save/{pid}_{index}"
    },
    {
      "uid": [
        "4872389[21-40]"
      ],
      "replace": false,
      "save": "save/{uid}/{pid}",
      "multi_save": "save/{uid}/{pid}_p{index}"
    }
  ]
}
```
