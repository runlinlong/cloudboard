# 先看这个：运行、理解和演示 Cloudboard

这是 AI 辅助草稿，来源见 `AI-DISCLOSURE.md`，提交前必须核对课程政策。不要把未做过的验证说成已经做过。

## 1. 项目放在哪里，使用什么环境

项目：`F:\pycharm\project\cloud`。

Python 解释器：`F:\pycharm\project\cloud\.venv\Scripts\python.exe`。

在 PyCharm 的 Python Interpreter 设置里选择这个现有解释器即可。不需要激活或修改其他项目的虚拟环境。Python 源代码用于本地阅读和测试；Docker 镜像内另外包含 Linux 下的 Python 和运行依赖。

三个程序的分工：

1. **Dashboard**：给浏览器显示网页、接收操作，并用 Python 的 requests 请求 Tasks。还负责计算进度统计。
2. **Tasks**：提供任务 REST API，校验输入，读取和写入数据库。
3. **PostgreSQL**：保存任务数据，不提供网页。

修改代码后，正在运行的容器不会自动跟着变。需要重新构建镜像，推送新标签，例如 `v2`，然后重新部署这个标签。

## 2. 打开项目

确认 Docker Desktop 本身处于正常运行状态。不要点击 Reset，不要重置 WSL，不要清理所有容器或镜像。原有 Home Assistant 作业与本项目分别管理。

本项目的 Kubernetes 浏览器地址：**http://127.0.0.1:18081**。

在 Docker Desktop 里，本作业的 Kubernetes 节点容器叫 `cloudboard-coursework-control-plane`，它内部运行上述服务。另一个作业的 `strange_kirch` 不属于本项目。三个名称以 `cloudboard-coursework-` 开头的 Compose 调试容器目前已停止，用于节省资源；不需要启动它们来访问 Kubernetes 版本。

下次使用时，如果 Docker Desktop 已正常运行，但本项目的节点容器处于停止状态，可以只启动这个已存在的节点：

```powershell
docker start cloudboard-coursework-control-plane
```

等待约半分钟再访问 18081。不要删除或重新创建现有集群来“启动”项目，否则可能丢失本地数据库。

另一个地址 http://127.0.0.1:18080 是可选的 Compose 调试环境；如果它被停止，不影响 18081 上的 Kubernetes 演示。两个环境的数据库彼此独立。

如果 18081 打不开，先在 PyCharm Terminal 进入项目目录，运行：

```powershell
kubectl --kubeconfig .local/kubeconfig --context kind-cloudboard-coursework -n cloudboard get pods
```

预期：一个 postgres Pod、两个 tasks Pod、两个 dashboard Pod，READY 为 `1/1`，STATUS 为 `Running`。Deployment 数量不同于 Pod 数量：Deployment 是管理副本的声明，Pod 是具体运行实例。

如有问题，继续看：

```powershell
kubectl --kubeconfig .local/kubeconfig --context kind-cloudboard-coursework -n cloudboard get events --sort-by=.lastTimestamp
kubectl --kubeconfig .local/kubeconfig --context kind-cloudboard-coursework -n cloudboard logs -l app=tasks --tail=30 --prefix
```

`ImagePullBackOff` 通常先查镜像名、公开权限和网络；`Pending` 先查资源与存储；`CrashLoopBackOff` 先查日志。**不要把重置 Docker 当成排错的第一步。**

## 3. 你至少要理解的代码

- `services/tasks/app.py` 的 `create_task()`：读取 JSON → 校验 → 参数化 INSERT → 返回 JSON 和 HTTP 201。
- 同文件的 `list_tasks()`：数据库查询结果变成 JSON。`update_task()` 用 PATCH 修改状态。
- `services/dashboard/app.py` 的 `call_tasks()`：`requests.request(...)` 就是在程序里调用另一个服务的 REST API。这是作业明确要求展示的能力。
- `dashboard()`：从 Tasks 获取数据，在 Dashboard 内计算完成数和百分比，因此 Dashboard 不只是静态网页。
- `services/dashboard/static/app.js`：浏览器使用 fetch 调用 Dashboard 的 API，然后更新界面。

请求路线：**浏览器 → Dashboard → Tasks → PostgreSQL**。Dashboard 不能直接查询数据库；只有 Tasks 持有数据库密码。

## 4. YAML 可以这样读

看 `k8s/app.yaml`，不必一次背下全部内容：

| 字段 | 作用 |
|---|---|
| `kind: Deployment` | 描述要运行的程序及其副本 |
| `replicas: 2` | 希望这个服务有两个实例 |
| `image` | 下载哪个容器镜像；模板由部署脚本填成 Docker Hub 地址 |
| `env` / `envFrom` | 通过环境变量告诉程序数据库在哪里等信息 |
| `kind: Service` | 给一组 Pod 提供稳定的访问地址 |
| `type: NodePort` | 让 Dashboard 通过节点端口接受访问 |
| `readinessProbe` | 判断这个实例能不能接业务请求 |
| `livenessProbe` | 判断程序是否仍能响应 |
| `resources` | 声明 CPU 和内存需求/上限 |
| `PersistentVolumeClaim` | 申请数据库使用的持久化存储 |
| `volumeMounts` | 把存储挂到数据库容器的目录中 |

`kind` 工具与 YAML 的 `kind:` 字段不是同一概念：前者创建本地 Kubernetes 集群，后者表示 Kubernetes 资源类型。

`k8s/kind.yaml` 把本机 `127.0.0.1:18081` 映射到节点端口 `30080`；Service 再把请求送到 Dashboard 的 `8000` 端口。

## 5. 演示独立扩容

```powershell
kubectl --kubeconfig .local/kubeconfig --context kind-cloudboard-coursework -n cloudboard scale deployment tasks --replicas=3
kubectl --kubeconfig .local/kubeconfig --context kind-cloudboard-coursework -n cloudboard get deployments,pods
```

此时 Tasks 应为三个副本，Dashboard 仍为两个。也可以单独把 Dashboard 改成三个。这里是**手动水平扩容**，没有实现自动 HPA，不要说系统会自动随流量扩容。

演示后恢复：

```powershell
kubectl --kubeconfig .local/kubeconfig --context kind-cloudboard-coursework -n cloudboard scale deployment tasks --replicas=2
kubectl --kubeconfig .local/kubeconfig --context kind-cloudboard-coursework -n cloudboard scale deployment dashboard --replicas=2
```

## 6. 演示持久化

先在网页新建一个有辨识度的任务，然后只重建**本项目数据库 Pod**：

```powershell
kubectl --kubeconfig .local/kubeconfig --context kind-cloudboard-coursework -n cloudboard rollout restart deployment/postgres
kubectl --kubeconfig .local/kubeconfig --context kind-cloudboard-coursework -n cloudboard rollout status deployment/postgres --timeout=180s
```

刷新网页，任务仍应存在。数据库启动期间可能暂时出现 503，稍后刷新即可。这个命令不重启 Docker 软件，也不影响另一个作业的容器。

数据不在应用内存中，而在 PostgreSQL 的 PVC 上。Pod 换了仍挂载同一个卷。但删除集群、清空 Docker 或磁盘损坏仍可能丢数据；持久化不等于备份。

## 7. 上传与录制

镜像仓库使用 `runlinlong/cloudboard-tasks` 和 `runlinlong/cloudboard-dashboard`，是否实际已上传见 `VERIFICATION.md`。

新版本发布：

```powershell
.\scripts\publish.ps1 -DockerHubUser runlinlong -Tag v2
.\scripts\deploy.ps1 -DockerHubUser runlinlong -Tag v2
```

镜像构建和上传之后，Pod 仍需要成功拉取并运行，不能只看上传命令成功。日志里有 method/path/status/duration_ms/instance，可用于展示两个服务之间的调用。

视频按 `VIDEO-PLAN.md` 录制，控制在 5–10 分钟。需要真正展示 Kubernetes、网页、日志和 YAML。你的讲解要建立在你理解代码和设计的基础上。

## 8. 常见答辩问题的思考方向

- 为什么拆成两个服务？说明职责边界和独立扩容，再承认这个小项目实际采用单体会更便宜。
- 多副本如何看到同样的数据？因为不依赖进程内存，访问同一任务数据库。
- 数据库为什么不扩容？题目允许单实例，关系型数据库的一致性与复制比无状态 API 复杂。
- 安全做了什么？输入校验、参数化 SQL、Secret、不记录密码、非 root 应用、浏览器文本转义。
- 没做什么？登录、权限、HTTPS、网络策略、备份、高可用和自动扩容。不要把计划说成已实现。
- 商业价值是什么？流量不均时独立扩容可能节省资源；团队职责可以分开，但系统和运维成本也会上升。
