# ManuAgent Web

面向现有 FastAPI MES 后端的 React 管理端，技术栈为 React、TypeScript、Vite、Ant Design 和 ECharts。

## 页面

- 产线与设备：按产线、设备状态和关键词筛选，查看设备状态。
- 报警与生产：按产线、设备、产品和日期查询生产数据，展示生产趋势与设备报警。
- 库存管理：展示全部库存和低库存风险。
- 维修工单：创建工单，并修改工单状态。

列表分页由前端完成，因为当前 FastAPI 列表接口返回数组；生产数据筛选会将参数传给 FastAPI。

## 本地启动

先在项目根目录启动后端：

```bash
uvicorn apps.api.app.main:app --reload
```

再启动前端：

```bash
cd frontend
npm install
npm run dev
```

打开 <http://127.0.0.1:5173>。Vite 默认将 `/api` 和 `/health` 代理到 `http://127.0.0.1:8000`。

如后端地址不同，复制 `.env.example` 为 `.env.local`，修改 `VITE_API_PROXY_TARGET`。独立部署时可设置 `VITE_API_BASE_URL` 为 FastAPI 完整地址，同时需要后端允许前端域名的 CORS。
