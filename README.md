# scrapy_redhat
the script to scapy the redhat KCS

</br>概述： </br><br> 1.此脚本使用selenium来直接通过webdriver调用firefox来进行爬取红帽KCS，由于页面中验证较多直接处理post请求较麻烦所以使用此方法，好在总数据量不大。 </br><br>2.数据库方面使用mysql作为存储数据库，依据页面内容使用8个字段(kcs id, 标题，环境，问题，解决方案，根本原因，分析步骤，私有内容 )。链接使用pymysql+sqlalchemy </br><br>3.脚本能够自动处理一段时间后自动验证密码问题，解决方法为抛异常自动重新登陆。能够自动处理一段时间后kcs列表hang死问题，解决方案为300秒返回空列表销毁浏览器对象并重新登陆。 </br><br>4.部分情况下红帽门户会出现无法登陆的情况，脚本依旧能够自动处理，解决方案任然是抛出异常自动重启。 </br>
      <br>5.本脚本能够自动跳过已经入库的kcs，依据kcs的id来进行判断。 </br>
      <br>6.默认情况下当出现连续10次登陆失败则主动退出，可能的原因为账户异常或者门户异常。 </br>
      <br>7.使用脚本时请配置翻墙或者内部系统代理，否则速度可能会降低90%。 </br>
      <br>8.脚本在爬取完成start到stop之内的所有kcs之后会自动退出exit(100)。 </br>
      <br>9.此脚本不会更新，随意使用，任何问题概不负责 </br>
