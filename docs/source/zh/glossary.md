# 术语表

当前架构设计草案 · 2026-11-16。

## 标准根时钟 / root

每个 epoch 唯一的时间和容量基准，ID 固定为 root。

## 子时钟 / Child clock

通过父周期比例与偏移派生节拍，继承标准单位，不增加容量。

## 信息同步组 / Synchronization group

绑定一个时钟，以共同窗口组织轨道，并配置交付策略和资源限额。

## 轨道 / Track

配置角色、方向、来源和格式，通过 sync_group_id 引用一个同步组。

## 标准帧单位 / Standard frame unit

容量计量单位，计入 A2RT 封装开销；不同于逻辑数据帧。

## 轨道数据帧 / Track data frame

一条轨道在一个组周期内至多提交的一份逻辑数据。

## 组信息帧 / Group information frame

同组同周期的不同轨道数据帧集合；每项分别引用 track_id。

## frame_seq

从零计数，标识固定窗口。迟到和重传不改变原窗口身份。

## role / direction / source_binding

分别表达内容角色、相对智能体端的流向及获准发布者，不能互相替代。

## delivery_policy

Profile 定义的交付策略配置；具体等待起点、完整性和超时动作由 Profile 解释。

## limits

确认后的组编码容量及每个接收端的队列上限，由 Core／Binding 落实。

## media_type / constraints / format_id

类型选择约束规则，constraints 声明具体契约，format_id 引用会话格式目录。

## epoch

冻结配置的作用域。重新协商后的新配置进入新 epoch，历史数据保留原解释。

## system

必选且唯一、固定 input 的系统通知轨道角色，发布方为可信环境或协调器。

## delivered_through

某接收端已连续交付的位置，不等于最新到达位置或实际消费完成。

## Profile

定义领域内容契约、输出和任务边界，以及播放、恢复、完整性和内容校验。
