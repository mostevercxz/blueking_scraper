角色登录流程梳理

```mermaid
sequenceDiagram
  Client->>FLServer:stIphoneRequestLoginCmd
  Note right of FLServer: checkFL
  FLServer->>Super:t_NewSession_Session
  Super-->>FLServer:t_NewSession_Session
  Note right of Super: checkSuper,返回login_ret
```


```
checkFL:
找到负载最小网关，且该网关在线人数小于1500人（配置）
```

```xml

<!--该服是否对外开启 影响Super killhup:SuperServer-->
<game_login_open_state>true</game_login_open_state>
<!--限制白名单登录 killhup:SuperServer-->
<specialloginstate>true</specialloginstate>
```

```
checkSuper:
1. 游戏不对外(game_login_open_state = false),只有超级账号,和白名单ip内机器人可以登录
2. 游戏对外,但限制了白名单登录，只有白名单账号（或超级账号），白名单ip内机器人可以登录
3. 游戏对外，没限制白名单登录
 * 判断账号是否被封禁
 * a
```

```mermaid
%% 时序图例子,-> 直线，-->虚线，->>实线箭头
 sequenceDiagram
   participant 张三
   participant 李四
   张三->王五: 王五你好吗？
   loop 健康检查
       王五->王五: 与疾病战斗
   end
   Note right of 王五: 合理 食物 <br/>看医生...
   李四-->>张三: 很好!
   王五->李四: 你怎么样?
   李四-->王五: 很好!
```