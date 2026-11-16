# 媒体类型、格式协商与约束

状态：当前架构设计草案；日期：2026-11-16。本章补充[时钟、信息同步组与轨道方案](./01-clock-sync-group-track-model.md)。以下 JSON 是设计示例；`example:` 和 `example.org` 引用代表说明用资源，接入时须提供实际定义。

A2RT 的内容格式统一由 `media_type` 和 `constraints` 描述。`media_type` 选择解码方式及对应的 A2RT 约束规则，`constraints` 提供该类型的具体配置与限制。JSON 内容结构也归入其中，通过 `constraints.schema` 内联定义或 `constraints.schema_ref` 引用，二者互斥。时钟和信息同步组负责节拍、同步与容量；角色和方向只定义在轨道上。Core 承载格式声明并检查通用结构，实际解码、内容校验及其失败处理由 Profile 定义、适配器或应用执行，职责见[第 03 章](./03-core-profile-responsibilities.md)。

## 1. 媒体类型决定约束规则

媒体类型采用 IANA 注册体系，例如 `application/json`、`image/png`、`image/jpeg`。不为每一种轨道另造一种 MIME 类型。[IANA Media Types](https://www.iana.org/assignments/media-types/)

HTTP 用 `Accept` 表达可接受的媒体类型及偏好，用 `Content-Type` 标识实际表示的类型。A2RT 参考这些概念，但使用自身的结构化配置，不要求通过 HTTP 传输，也不将下面的 JSON 当作 HTTP 头语法。[RFC 9110：Content-Type](https://www.rfc-editor.org/rfc/rfc9110.html#section-8.3)、[Accept](https://www.rfc-editor.org/rfc/rfc9110.html#section-12.5.1)

格式描述只有两个业务字段：

| 字段 | 定义 |
| --- | --- |
| `media_type` | 不含参数的 `type/subtype`，选择该类型对应的解码与 A2RT 约束规则 |
| `constraints` | 对象，包含该类型的配置、结构校验及接收限制；没有额外要求时使用 `{}`，但仍须满足该类型的必填规则 |

约束字段的名称、类型、单位和含义，由格式规范按媒体类型定义，并由选定的协议/Profile 版本固定。Profile 选择具体规则，明确谁在何时验证实际内容；Core 不要求内置相应解码器或业务校验器。例如，图片规则识别宽高，音频规则识别采样率和声道数，JSON 规则识别内容 Schema。双方不需要再为标准约束单独协商一份约束 Schema 引用。

媒体参数统一放入 `constraints`，内容结构定义放入 JSON 的 `constraints.schema` 或 `constraints.schema_ref`。后者只引用实际 JSON 内容的 Schema，不是引用 `constraints` 自身的规则。

这些字段是 A2RT 的配置，并不会自动成为 HTTP 媒体类型参数。对接 HTTP、RTP 等传输时，由绑定层将适用字段映射为相应标准参数；尺寸、字节上限和 JSON Schema 等保留为 A2RT 约束。容器、编解码器及传输压缩仍按各自规范处理，不能因为统一字段就混淆其含义。

## 2. 格式目录与轨道引用

会话配置通过 `formats` 保存完整格式描述，轨道通过 `format_id` 引用其中一项。`format_id` 是 epoch 内唯一的本地标识，不是第三种格式规则，也不是 IANA 注册名。

```json
{
  "formats": [
    {
      "format_id": "jpeg_720p_1mb_v1",
      "media_type": "image/jpeg",
      "constraints": {
        "max_width": 1280,
        "max_height": 720,
        "max_encoded_bytes": 1000000
      }
    },
    {
      "format_id": "pcm16be_mono24k_v1",
      "media_type": "audio/L16",
      "constraints": {"rate": 24000, "channels": 1}
    },
    {
      "format_id": "canvas_events_v1",
      "media_type": "application/json",
      "constraints": {
        "schema_ref": "example:canvas-event-v1",
        "max_encoded_bytes": 65536
      }
    }
  ]
}
```

轨道通过 `format_id` 引用目录项，不能单独保存或覆盖 `constraints`。多个轨道可以共享同一目录项；媒体类型相同但约束不同的格式，应使用不同的目录项和 `format_id`，避免同一个引用具有多套解释。

示例中的 `audio/L16` 是有符号 16 位、大端字节序的线性 PCM；A2RT 将 `rate`、`channels` 统一放入 `constraints`，使用正整数表达精确采样率和声道数，传输绑定再转换为媒体参数。选定配置须明确 `rate`；本方案将未提供的 `channels` 按媒体默认值 1 补齐后确认。小端 `pcm_s16le` 不能直接标成 `audio/L16`。[RFC 2586 §3](https://www.rfc-editor.org/rfc/rfc2586.html#section-3)、[IANA audio/L16 参数](https://www.iana.org/assignments/media-types/audio/L16)

## 3. JSON 的内联 Schema 与引用

`application/json` 选择通用 JSON 解析及约束规则，业务内容的结构通过以下两种方式之一声明。

### 3.1 内联定义

`constraints.schema` 直接包含 JSON Schema，供 Profile 指定的实现校验解码后的实际 JSON 载荷，不是外层格式描述或 A2RT 消息信封。Core 可以承载该定义而不执行内容校验：

```json
{
  "media_type": "application/json",
  "constraints": {
    "schema": {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "$id": "https://example.org/schemas/canvas-state.v1.schema.json",
      "type": "object",
      "properties": {
        "active_tool": {"type": "string"},
        "selected_element_ids": {
          "type": "array",
          "items": {"type": "string"},
          "uniqueItems": true
        }
      },
      "required": ["active_tool", "selected_element_ids"],
      "additionalProperties": false
    },
    "max_encoded_bytes": 65536
  }
}
```

例如，下面的载荷满足该内容 Schema；缺少必填字段、元素 ID 不是字符串或出现未声明字段则不满足：

```json
{
  "active_tool": "rectangle",
  "selected_element_ids": ["shape_1", "shape_2"]
}
```

`max_encoded_bytes` 独立检查该载荷序列化为 UTF-8 后的字节数，不包括配置中的 Schema 定义。配置本身仍须遵守配置传输及资源预算。

### 3.2 引用定义

已由双方维护的 Schema 可以通过 `constraints.schema_ref` 引用：

```json
{
  "media_type": "application/json",
  "constraints": {
    "schema_ref": "https://example.org/schemas/canvas-state.v1.schema.json",
    "max_encoded_bytes": 65536
  }
}
```

引用必须绑定到不可变的内容版本；`.schema.json` 是文件命名惯例，不是强制后缀。Schema 可以来自预置资源、Profile 包或其他约定资源，无需逐帧下载。Profile 明确引用基准、解析时机、能力确认方式及解析失败的处理；负责校验的实现无法取得定义时，不能报告内容已经通过该 Schema。仅转发引用的 Core 不必联网获取资源，不能在同一引用下悄悄更换定义。

### 3.3 互斥与校验规则

| `constraints.schema` | `constraints.schema_ref` | 处理 |
| --- | --- | --- |
| 存在 | 不存在 | 向 Profile 实现提供内联定义 |
| 不存在 | 存在 | 由 Profile 实现按约定解析并使用该定义 |
| 存在 | 存在 | 配置无效，直接拒绝；即使声称两者相同也不允许 |
| 不存在 | 不存在 | 仅采用通用 JSON 规则及其他约束；需要固定领域结构的 Profile 必须要求二选一 |

互斥按字段是否存在判断，不按值的真假判断。JSON Schema 可以是对象或布尔值，因此 `schema: false` 仍然算存在；`null` 或包含 JSON 文本的字符串不能充当内联 Schema。[JSON Schema Core：Schema 定义](https://json-schema.org/draft/2020-12/json-schema-core#section-4.3)

本章示例使用 JSON Schema Draft 2020-12，不设为 Core 的全局默认。Profile 定义采用的方言、`$schema` 省略时的解释、`format` 等可选校验行为、校验时机和失败处置；适配器或应用按该约定实现。内联及引用方式采用同一套 Profile 规则。Schema 内的 `$ref` 是 JSON Schema 自身的复用机制，不受外层二选一规则禁止；其解析规则也由 Profile 定义。

内容 Schema 只描述其声明的结构与校验条件，不能单凭校验通过就推断工具语义或执行权限。`type`、`required`、`enum` 等仍是声明的内容契约，但履行该契约的是 Profile 指定的校验实现；邮箱、对象 ID 或业务参数是否有效不由 Core 判断。只支持 JSON 解析，不等于支持所有业务 Schema。

assistant 内容的事件集合、参数、输出标识及结束表达也由 Profile 的契约定义，通过所选格式声明。`application/json`、轨道角色或某个 `format_id` 均不隐含 A2RT 标准的 assistant 事件类型；Core 不要求 Schema 必须包含生成标识、工具调用或结束事件。

同样，system 轨道的事件集合、字段、语义和内容 Schema 由 Profile 定义。采用 JSON 时，Profile 通过 `constraints.schema` 或 `constraints.schema_ref` 提供自己的契约，A2RT 不强制通用系统事件 Schema。示例中的 `system_events_v1` 只是会话内格式 ID，不能仅凭该名称认定两端兼容，也不能据载荷中的某个事件名称自动更新核心会话状态。

两种方式的声明都在配置协商时固定，后续数据帧只引用轨道。解析及内容验证按 Profile 约定进行，Core 只检查声明结构、引用绑定和二选一关系。改变内联定义或引用的内容版本，必须重新协商并切换配置 epoch，不能重新解释旧数据。

## 4. 能力声明与格式选择

接收端按轨道声明 `accept`，发送端声明自己能够产生的候选格式。每个 `accept` 候选都使用相同的 `media_type`、`constraints` 结构，可另带协商偏好 `q`。限制放在各自候选内，不在能力声明顶层再放一份跨类型的约束。

```json
{
  "receiver_id": "model_adapter",
  "track_id": "board_image",
  "accept": [
    {
      "media_type": "image/png",
      "constraints": {
        "max_width": 1280,
        "max_height": 720,
        "max_encoded_bytes": 1000000
      },
      "q": 1.0
    },
    {
      "media_type": "image/jpeg",
      "constraints": {
        "max_width": 1280,
        "max_height": 720,
        "max_encoded_bytes": 1000000
      },
      "q": 0.8
    }
  ]
}
```

本阶段的协商规则如下：

1. `accept` 必须非空，每项声明明确的媒体类型；暂不引入 `image/*`、`*/*` 等通配符。媒体类型按其规范比较；A2RT 的约束键名按本章固定拼写，不能擅自改写字段或 Schema 标识。
2. Core 检查候选的通用结构、格式引用及 `schema`/`schema_ref` 互斥。Profile 实现根据 `media_type` 确认其支持的约束规则、内容 Schema 及处理能力，负责具体字段和语义校验；不能把不支持或尚未确认的能力报告为已支持。
3. `q` 表示偏好，范围为 0～1，最多三位小数，省略为 1，0 表示不接受；它不是图片压缩质量，不属于内容约束。这沿用 HTTP 的权重含义。[RFC 9110 §12.4.2](https://www.rfc-editor.org/rfc/rfc9110.html#section-12.4.2)
4. Profile 实现确认发送能力、接收能力及内容限制，Core／Binding 检查通用部署预算并承载协商结果。已声明的约束仍须由负责方履行；例如图片上限及精确采样率的匹配由相应格式处理器判断。支持多个精确配置时可列出多个候选，不由 Core 自动猜测业务转换方式。
5. JSON 的内容契约必须由双方确认支持；不能只因媒体类型相同就认为 Schema 兼容，也不要求实现通用的任意 Schema 等价性或包含关系求解器。内联和引用可以在确认对应同一内容契约后匹配，最终选定项仍只能保留一种表达。
6. 满足全部硬性要求后再考虑 `q`；多项同权重时由 Profile 或协商方选定，明确告知双方。选定的完整格式描述写入 `formats`，轨道引用其 `format_id`。同名 ID 不自动代表跨会话兼容。
7. 没有兼容项、约束无法满足或双方未确认最终配置时，协商失败；不能静默放宽限制或发送其他类型。所需轨道协商失败时，不能激活依赖它的信息同步组配置。

假设上例中只有 JPEG 能在资源预算内满足限制，双方确认第 2 节的 `jpeg_720p_1mb_v1` 后，轨道配置如下；`interaction` 引用已声明的信息同步组，`environment` 是该示例 Profile 声明的环境数据角色。画布图像属于普通环境数据，不属于第 04 章的 system 控制事件：

```json
{
  "track_id": "board_image",
  "sync_group_id": "interaction",
  "role": "environment",
  "direction": "input",
  "format_id": "jpeg_720p_1mb_v1",
  "source_binding": ["canvas_renderer"],
  "content_policy": "snapshot_or_explicit_hold"
}
```

第一阶段，双向轨道选择双方都能编码和解码的同一格式及共同约束，两端能力分别验证；两个方向共享每轨每周期最多一个数据帧的上限，发布安排按第 01 章约定。需要不同格式或约束，或者需要双方在同周期分别发布数据帧时，拆成两条单向轨道。[system 系统轨道](./04-system-track-and-lifecycle.md)在会话配置中必选且唯一，固定为单向输入，不适用双向协商，也不能为不同格式创建多条 system 角色轨道；其唯一选定格式由 Profile／双方确认。系统输入事件与 assistant 输出事件分别使用自己的格式声明，模型结束信号不会因同为 JSON 而进入 system 轨道。能力清单关联可信端点身份，不额外定义角色或方向；允许谁发送、谁接收仍由轨道及来源绑定确定。

选定格式与约束在 epoch 内冻结。更改配置须重新协商并切换 epoch；旧 epoch 的在途数据和录像继续按原配置解释。这里冻结的是格式及限制，不是要求上限范围内的每张图片都具有相同像素尺寸。

## 5. 按媒体类型解释 constraints

| 适用类型 | 字段及规则 |
| --- | --- |
| 通用 | `max_encoded_bytes`：正整数，一个轨道数据帧的完整编码载荷字节上限，不按传输分片分别计算 |
| `image/jpeg`、`image/png` | `width`、`height`、`max_width`、`max_height`：正整数，单位为像素；精确值与上限必须可同时满足 |
| `audio/L16` | `rate`、`channels`：正整数，分别为精确采样率和声道数；取值须符合媒体规范及双方能力 |
| `application/json` | `schema`：内联 JSON Schema；`schema_ref`：非空资源引用字符串；二者互斥，用于校验实际 JSON 内容 |
| 其他媒体类型 | 由对应的 A2RT 格式规范或 Profile 扩展明确字段、类型、单位、默认值及验证逻辑 |

通用规则与选中类型的规则共同生效，不需要独立的媒体参数或约束 Schema 字段。图片约束不能随意用于音频，JSON 的 `schema` 字段也不能未经定义用于 JPEG。采用 JSON 编码的自定义媒体类型如需复用这些规则，须在其格式规范中明确；仅有 `+json` 后缀不代表双方已理解领域语义。

扩展通过选定的协议/Profile 版本声明其适用媒体类型及规则，双方确认后启用；不能重定义标准字段或暗中改变同一类型的解释。对新增内容约束，Profile 指定的参与方须确认支持，不能忽略强制字段后宣称满足约束；通用转发节点不必理解这些业务字段。Profile 实现可在内部使用 Schema 验证 `constraints`，线上的格式描述统一保持 `media_type` 与 `constraints` 两个业务字段。

### 5.1 720P 与 1 MB

前面的图片约束表示：每张图片宽度不超过 1,280 像素、高度不超过 720 像素，完整 JPEG 或 PNG 的编码载荷不超过 **1,000,000 字节**。它允许更小尺寸，不强制 16:9 比例。

如果要求每张图片恰好为 1280 × 720，应改用精确尺寸：

```json
{
  "media_type": "image/jpeg",
  "constraints": {
    "width": 1280,
    "height": 720,
    "max_encoded_bytes": 1000000
  }
}
```

`width`、`height` 是精确值，`max_width`、`max_height` 是上限；若同时出现，两者必须一致可满足。不能只写 `720p` 而让双方猜测是固定尺寸、最大尺寸还是一种视频模式。实际尺寸由 Profile 指定的媒体处理器按解码得到的原始像素矩阵验证；若应用需要旋转、裁剪或展示坐标，还须由内容契约明确，不能暗中更换计量口径。

本例的 MB 按十进制计量：1 MB = 1,000,000 字节；若要求 1 MiB，应填 1,048,576。编码大小不等于解码后的像素内存大小；承担内容校验的接收实现按 Profile 检查编码长度与实际像素尺寸，Core 不需要解码图片。

### 5.2 轨道数据帧的载荷与分片

`max_encoded_bytes` 针对一个轨道数据帧的完整编码载荷：静态图片是一张完整图片；音频是内容契约定义的一段采样；JSON 是一份完整 JSON 值，内部结构由内容 Schema 定义。一个周期内每条轨道最多提交这一份数据帧；Profile 不能允许同轨同周期多个独立数据帧，再通过数组、批次或不同消息封装规避上限。载荷包含多个业务字段或采样点不增加数据帧名额，各格式必须明确整份载荷的边界，不能通过重新切分绕过字节上限或帧数限制。

大小包含该内容表示本身的全部字节，例如 JPEG/PNG 文件内的头部和元数据、JSON 序列化后的 UTF-8 字节；不含 A2RT 信封、分片头、底层传输头，以及传输层额外增加的 Base64 包装或压缩。绑定层须规定如何还原计量对象。A2RT 自身开销仍按 `root.size_scope` 计入标准帧预算，不能因为未计入媒体上限而免计容量。

一张 1.2 MB 图片即使拆成若干个小于 1 MB 的分片，也违反 1 MB 上限。一张符合上限的图片则可以跨多个标准帧单位发送，所有分片仍属于同一轨道、同一周期的同一数据帧；Binding 报告重组结果，Profile 实现按约定判断它是否满足同步交付条件。一个组信息帧可以包含不同静态图片轨道各自的一张图片，每张图片的上限及整个信息帧的 `limits.max_frame_units` 必须同时满足；同一静态图片轨道不能在同周期追加第二张图片数据帧。重传保留原帧身份和内容，不重新占用位置或重复交付。

发送方按“谁发送谁负责”的原则准备并校验满足 Profile 契约的内容，对发送内容的格式、时间与已声明约束负责；接收方核验实际载荷，发现不符按 Profile 丢弃、隔离或采取其他约定措施，若选择补交则由发送方负责纠正或重新采集。接收核验不转移发送方责任，Core 也不凭声明的尺寸代替业务校验。允许的缩放、编码质量调整、失败后的拒绝/降级/恢复，以及是否通知、使用自定义轨道还是其他通道，均由 Profile 定义；Core 不强制格式错误消息或错误码。通用资源预算及分片重组边界仍由 Core／Binding 执行，不能把未校验或已超限报告为已满足契约。

## 6. 与时钟、信息同步组及反馈的关系

格式定义不增加时钟、角色或方向。音频采样率、视频编码帧率和组信息帧频率是不同概念；图片尺寸上限也不决定图片每秒发送多少次。

媒体兼容只是会话建立条件之一，必须同时检查标准根时钟及信息同步组容量。例如每秒 10 张、每张实际 1 MB 的图片，仅图片载荷就需要 10 MB/s，尚未计入其他轨道和 A2RT 开销。第 01 章示例中的每帧 64 个 1,024 字节单位，不能承载一张接近 1 MB 的图片；本章的大小限制示例不自动增加该配置的预算。若承诺每周期都能发送最大内容，资源分配必须覆盖该上限；否则须另行约定可验证的流量或调度限制。

Profile 定义内容是否满足约束、要求哪种就绪阶段，以及失败后如何影响同步交付。适配器或应用维护实际结果；若选择通知，可用轨道、来源、epoch 和信息帧等通用引用关联目标，通知格式及载体由 Profile 约定。Core 不强制错误控制消息或某一种恢复算法。记录应区分已收到、已校验、已交付等实际阶段；直接丢弃不能把缺失计为成功交付，取消与恢复流程也不能因缺失媒体永久阻塞。

面向模型的格式处理须在模型消费前达到已确认的输入契约：发送端负责准备与发送前检查，接入层处理接收后的重组、必要解码及校验。模型接口可以原生接受已约定的编码媒体或流式片段，不要求所有媒体都预先转换为原始数据；但不能要求模型解析传输分片、修补损坏载荷或自行完成跨轨对齐。Profile 允许的部分内容与业务错误按其语义交付，内部格式处理失败由运行时处理，具体边界见[第 03 章 §1.2](./03-core-profile-responsibilities.md#12-面向模型的信息交付边界)。

媒体类型与约束声明不改变已记录的身份、来源时间和实际交付事实。保持、静音、内容缺失和消费规则由 Profile 解释并落实，Core 负责保存相应引用与状态关联。

## 7. 后续实现与验证边界

Core 实现格式目录及引用、通用声明结构与互斥检查，承载接收能力和协商结果；Profile 实现负责按媒体类型处理约束、解析 JSON Schema 并校验媒体与领域内容。错误的处置、是否通知及通知方式按[第 03 章 §1.3](./03-core-profile-responsibilities.md#13-默认业务通道与异常处置)由 Profile 选择；通用引用用于定位相关轨道和信息帧，不构成必发的错误消息。Canvas 的图片、音频、事件、状态分别绑定适当格式；每 actor 一个任务及同步交付属于 Canvas 的领域选择。

Core 验证通用结构、格式引用、schema/schema_ref 互斥、方向、配置版本隔离及每轨每周期最多一个数据帧；分片、重传、双向或多来源不增加帧名额。Profile 的验证覆盖候选能力兼容、媒体类型与约束匹配、内联 Schema 正反例、引用解析、Schema 版本、双向能力、尺寸冲突、完整图片超限但分片未超限、实际内容与声明不符，以及各自的失败处置。配置片段用于说明设计，不能代替对实际实现的上述校验。
