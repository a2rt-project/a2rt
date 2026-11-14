# 独立轨道、更新语义与时间

## 1. 轨道与 stream

六条逻辑轨道见 [README](./README.md)。一个 stream 只属于一条轨道，并绑定一个来源、一套内容 Schema 和一个来源时钟。audio stream 还固定编码、采样率、通道数及原点；变更这些参数需要创建新 stream。

每个 stream 的 seq 独立从 1 递增。seq 是**更新记录序号**，不是视频帧号或音频采样号；不同 stream 的相同 seq 不表示同时发生。assistant.events 由 output.event 构成，逻辑 seq 使用 output_seq，不再在 updates 中复制一份。环境事件使用 updates，原事件及回执通过 event_id 关联。

同一个反馈可以只有新声音，也可以只有结果或新画面。某轨道没有更新时可以不出现在 updates 中；接收方保留缓存，不清空内容、不移动媒体游标、不认为当前事实已被再次核实。初始清单表明轨道是否启用，不能用“从未收到”猜测轨道被禁用。

## 2. TrackUpdate

通用字段为 track、stream_id、source_id、seq、time、mode，以及各模式的特定字段。time 是这条更新的来源时刻；message.sent_at 是发送时刻。内容结构由 stream.format 和协商清单确定。

| mode | 必填内容 | 消费方式 |
| --- | --- | --- |
| new | data | 新的观察、事件或音频区间，按对应 Schema 消费一次 |
| reuse | ref_seq、verification | 引用同 stream 之前某条 new 的内容；适用于视觉／领域状态 |
| empty | reason | 本轮无新增、尚未就绪或不可用；缓存与媒体游标保持 |
| gap | data={unit, from, to, reason} | 明确一段数据缺失，范围为 [from,to)；不是静音或成功 noop |

empty.reason 为 no_new_data / not_ready / unavailable。它是观察可用性说明，不是声音、图像或领域数据本身。new 的空列表／空选区是有效事实，含义不同。

reuse.verification 为 null 时，只复用历史上下文，没有确认当前内容仍一致。若重新确认了外观或状态未变，verification 必须包含核验时刻 at 及相应 state_refs。原 new 的来源时间和版本不变。不能单凭“没收到变化”生成 verification。

音频和事件流禁止 reuse：之前的音频可留在模型上下文里，但不能当作新的输入采样再次处理或播放。事件历史也不能被重新执行。缺少新声音用省略／empty；确实有一段静音则用 new 音频数据中的 silence。

gap 的 unit 可以是 samples 或 time_us；其范围属于该 stream 的采样／时间坐标。音频 gap 推进已覆盖采样范围但标记为缺失；time_us 缺口不授予虚构的事件或状态。消息序号丢失由 binding 恢复或触发 resync，不能靠业务 gap 掩盖未收到的回执。

## 3. 状态与画面的版本

`environment.state` 由多个独立 stream 承载：core.result、core.playback 和 Profile 领域状态等。领域状态的通用容器为 `{schema_id, revision, value}`；value 完全按 Profile 定义，空选区、对象、组、窗口等均不是核心字段。本版基础配置使用每个状态命名空间的完整快照；增量编码须另行协商可还原的基础与补全机制，不默认把缺少字段当作删除。

core.visual 内容为资源引用、媒体类型、宽高及 source_state_refs。引用字段的 `{stream_id, revision}` 描述这张画面实际基于的领域状态。真实相机可以没有结构化状态对应项；不能编造一个匹配版本。

引用的状态版本可以尚未交付：图像先到时立即提供图像，保留待解析版本引用，不为了满足引用而等待状态轨。引用必须指向已注册的领域状态 stream；收到相应版本后再解析关联。reuse 的核验依据也允许先于相应状态内容交付。无法取得关联内容不影响独立模态消费，但不能据此声称已完成跨模态内容核验。

状态 r12 可以先到，基于 r11 的图像稍后到。两者可以一起提供给模型，但必须保留各自版本；不能声明它们是同一快照。执行依赖图像的操作时，Profile 负责检查目标和坐标映射是否仍适用。

## 4. 时钟

使用 `{clock_id, t_us}`；t_us 是该单调时钟起点后的整数微秒，不是 Unix 时间。会话注册采集、模型产出、执行和播放时钟。不同 clock 不可直接相减。

绑定层维护显式时钟映射：源／目标 clock_id、对应锚点、比例或漂移估计、有效范围和误差上界。映射变化需有版本并留存录像；未知映射时不能声称精确同步。示例采用显式共同原点的单时钟，只为说明因果顺序。

每条数据分别保留采集、应用、呈现等相应时间。反馈 sent_at 不覆盖它们；不再要求一个全局 capture_cutoff 覆盖所有轨道。

## 5. 音频片段

core.audio 数据：start_sample、sample_count、content、requires_events。content 为 `{kind: "media", ref: ...}` 或 `{kind: "silence"}`；sample_count > 0，区间为 [start_sample, start_sample + sample_count)。requires_events 是该声音片段显式依赖的事件 ID，可为空。

采样时长为 sample_count/sample_rate；起点由 stream 的音频原点与采样位置决定。网络传输、模型推理和消息间隔都不能用来推算声音长度。PCM16 数据长度为 sample_count × channels × 2；其他编码按协商格式校验解码采样范围。

各 stream 独立维护接收、解码、呈现、模型已消费游标；不同方向的音频没有等长要求。没有音频更新的一轮无需生成静音凑齐窗口。下一块接续上一块的样本区间，确有中断必须报告 gap 或关闭旧流、新建流，不可隐瞒丢样。

接收、解码与消费不同：资源引用已到但资源未到时，该内容未就绪。可以先发布其他轨道并报告 empty/not_ready；不要发布不可消费的 new 后要求整个模型轮次等待。大资源绑定须提供字节边界、完整性校验、大小限制和独立就绪通知。

## 6. 声音与操作的局部同步

Event.timing 有两种：

- immediate：不依赖音频，获准后尽快应用；纯视觉或纯操作模式也可以运行。
- audio：指定 assistant.audio 的 stream_id、sample 与 late_policy。调度器按**实际播放采样位置**呈现事件。late_policy 为 reject 或 apply_now；后者必须回报迟到及真实应用时刻，不能伪称原时刻执行。

需要教学音画配合时，相关音频片段通过 requires_events 引用事件；调度器在播放该片段前须取得事件、完整片段并确认事件可调度。这里只等待显式关联项；其他声音、环境采集和反馈仍继续。等待超时报告失败／未知并停止相关未播放声音。

这不是“音频等待事件执行完成、事件又等待音频播放”的循环等待：先确认双方已就绪并登记调度，再启动声音，在指定采样位置应用事件。声明的 sample 必须落在引用该事件的相关片段范围内；没有关联片段的 audio timing 不可执行。

不支持可控应用时刻的远程工具不得宣称精确对齐。可以先报告实际结果，再生成相关讲解；这与支持精确调度的指针／本地操作能力分开声明。目标变化或操作失败时停止关联的未播放声音，已经播出的声音不能假装撤回。

流式音频可以跨多个 media 消息到达；片段到齐后立即可用，不等待整句话。v0.2 的“完整片段”是解码可消费的最小协商片段，不是整段录音。
