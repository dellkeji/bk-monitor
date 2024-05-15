/*
 * Tencent is pleased to support the open source community by making
 * 蓝鲸智云PaaS平台社区版 (BlueKing PaaS Community Edition) available.
 *
 * Copyright (C) 2021 THL A29 Limited, a Tencent company.  All rights reserved.
 *
 * 蓝鲸智云PaaS平台社区版 (BlueKing PaaS Community Edition) is licensed under the MIT License.
 *
 * License for 蓝鲸智云PaaS平台社区版 (BlueKing PaaS Community Edition):
 *
 * ---------------------------------------------------
 * Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
 * documentation files (the "Software"), to deal in the Software without restriction, including without limitation
 * the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and
 * to permit persons to whom the Software is furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all copies or substantial portions of
 * the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
 * THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
 * CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
 * IN THE SOFTWARE.
 */

import { computed, defineComponent, PropType } from 'vue';

import { Popover } from 'bkui-vue';
import { bkTooltips } from 'bkui-vue/lib/directives';

import CrossAppTag from '../../../static/img/cross-app-tag.png';
import { SPAN_KIND_MAPS } from '../../../store/constant';
import { useTraceStore } from '../../../store/modules/trace';
import { useChildrenHiddenInject, useSpanBarCurrentInject } from '../hooks';
import ArrowRightShapeIcon from '../icons/arrow-right-shape.svg';
import ErrorIcon from '../icons/error.svg';
import { Span } from '../typings';
import SpanBar from './span-bar';
import SpanTreeOffset from './span-tree-offset';
import Ticks from './ticks';
import TimelineRow from './timeline-row';
import TimelineRowCell from './timeline-row-cell';
import { createViewedBoundsFunc, formatDuration, ViewedBoundsFunctionType } from './utils';

import './span-bar-row.scss';

const SpanBarRowProps = {
  className: {
    type: String,
    required: false,
    default: '',
  },
  color: {
    type: String,
  },
  columnDivision: {
    type: Number,
    default: 0,
  },
  isChildrenExpanded: {
    type: Boolean,
  },
  isDetailExpanded: {
    type: Boolean,
  },
  isMatchingFilter: {
    type: Boolean,
  },
  isFocusMatching: {
    type: Boolean,
  },
  isActiveMatching: {
    type: Boolean,
  },
  isHaveRead: {
    type: Boolean,
  },
  onDetailToggled: Function as PropType<(spanID: string) => void>,
  onLoadCrossAppInfo: Function as PropType<(span: Span) => void>,
  numTicks: {
    type: Number,
    default: 0,
  },
  rpc: {
    type: Object,
    required: false,
    default: null,
  },
  noInstrumentedServer: {
    type: Object,
    required: false,
    default: {
      color: '',
      serviceName: '',
    },
  },
  showErrorIcon: {
    type: Boolean,
  },
  // getViewedBounds: Function as PropType<ViewedBoundsFunctionType>,
  // traceStartTime: {
  //   type: Number
  // },
  span: {
    type: Object as PropType<Span>,
  },
  focusSpan: Function as PropType<(spanID: string) => void>,
  bgColorIndex: {
    // 层级背景色索引
    type: Number,
    required: true,
  },
};

export default defineComponent({
  name: 'SpanBarRow',
  directives: { bkTooltips },
  props: SpanBarRowProps,
  emits: ['toggleCollapse'],
  setup(props, { emit }) {
    const { traceTree: trace } = useTraceStore();

    const spanBarCurrentStore = useSpanBarCurrentInject();
    const childrenHiddenStore = useChildrenHiddenInject();

    // 是否跨应用调用 span

    const crossRelationInfo = computed(() =>
      Object.keys(props.span?.cross_relation || {}).length ? props.span?.cross_relation : false
    );
    const ellipsisDirection = computed(() => useTraceStore().ellipsisDirection);
    // 是否显示耗时
    const showDuration = computed(() => useTraceStore().traceViewFilters.includes('duration'));

    const getViewedBounds = (): ViewedBoundsFunctionType => {
      const [zoomStart, zoomEnd] = spanBarCurrentStore?.current.value as [number, number];

      return createViewedBoundsFunc({
        min: trace?.startTime || 0,
        max: trace?.endTime || 0,
        viewStart: zoomStart,
        viewEnd: zoomEnd,
      });
    };

    const detailToggle = () => {
      props.onDetailToggled?.(props.span?.spanID);
    };

    const childrenToggle = () => {
      childrenHiddenStore?.onChange(props.span?.spanID || '');
    };

    const handleClick = (e: Event, hasChildren: boolean) => {
      e.stopPropagation();
      if (hasChildren) {
        childrenToggle();
      } else {
        props.onLoadCrossAppInfo?.(props.span as Span);
      }
    };

    const handleToggleCollapse = (e, groupID, status) => {
      e.stopPropagation();
      emit('toggleCollapse', groupID, status);
    };

    return {
      detailToggle,
      childrenToggle,
      handleClick,
      getViewedBounds,
      crossRelationInfo,
      ellipsisDirection,
      showDuration,
      handleToggleCollapse,
    };
  },

  render() {
    const {
      className,
      color,
      columnDivision,
      isChildrenExpanded,
      isDetailExpanded,
      isMatchingFilter,
      isFocusMatching,
      isActiveMatching,
      isHaveRead,
      numTicks,
      rpc,
      noInstrumentedServer,
      showErrorIcon,
      bgColorIndex,
      span,
    } = this.$props;
    const {
      span_id: spanID,
      duration,
      hasChildren: isParent,
      operationName,
      process: { serviceName },
      kind,
      is_virtual: isVirtual,
      source,
      ebpf_kind: ebpfKind,
      ebpf_thread_name: ebpfThreadName = '',
      ebpf_tap_side: ebpfTapSide = '',
      ebpf_tap_port_name: ebpfTapPortName = '',
      group_info: groupInfo,
      is_expand: isExpand,
    } = span as Record<string, any>;
    /** 折叠节点的耗时取自 group_info.duration */
    const realDuration = groupInfo && groupInfo.id === spanID && !isExpand ? groupInfo.duration : duration;
    const label = this.showDuration ? formatDuration(realDuration) : '';

    const viewBounds = this.getViewedBounds?.()(
      span?.startTime as number,
      (span?.startTime as number) + (realDuration as number)
    );

    const viewStart = viewBounds?.start;
    const viewEnd = viewBounds?.end;
    const isOddRow = (bgColorIndex as number) % 2 !== 0;

    const displayServiceName =
      source === 'ebpf' ? (ebpfKind === 'ebpf_system' ? ebpfThreadName : ebpfTapSide) : serviceName;

    const displayOperationName =
      source === 'ebpf' ? (ebpfKind === 'ebpf_system' ? operationName : ebpfTapPortName) : operationName;
    const labelDetail = `${displayServiceName}::${displayOperationName}`;
    let longLabel;
    let hintSide;
    if (viewStart && viewEnd && viewStart > 1 - viewEnd) {
      longLabel = `${labelDetail}${label ? ` | ${label}` : ''}`;
      hintSide = 'left';
    } else {
      longLabel = `${label ? `${label} | ` : ''}${labelDetail}`;
      hintSide = 'right';
    }

    return (
      <TimelineRow
        className={`
          span-row
          ${className || ''}
          ${isOddRow ? 'is-odd-row' : ''}
          ${isDetailExpanded ? 'is-expanded' : ''}
          ${isFocusMatching ? 'is-focus-matching' : ''}
          ${isActiveMatching ? 'is-active-matching' : ''}
          ${isHaveRead ? 'is-have-read' : ''}
          ${isMatchingFilter ? 'is-matching-filter' : ''}
        `}
      >
        {isHaveRead && (
          <Popover
            content={this.$t('已读')}
            placement='left'
            theme='dark'
          >
            <span class='have-read-mark'></span>
          </Popover>
        )}
        {this.crossRelationInfo ? (
          <TimelineRowCell
            style={{ cursor: 'pointer' }}
            width={1}
            className='span-view cross-app-span'
          >
            <div
              class={[
                'span-name-wrapper',
                {
                  'is-matching-filter': this.isMatchingFilter,
                  'is-disabled': !this.crossRelationInfo.permission,
                },
              ]}
              v-authority={{ active: !this.crossRelationInfo.permission }}
            >
              <SpanTreeOffset
                childrenVisible={isChildrenExpanded}
                showChildrenIcon={true}
                span={span}
                onClick={(e: Event) => this.handleClick(e, isParent)}
              />
              <a class='cross-span-name'>
                <img
                  class='cross-tag'
                  alt=''
                  src={CrossAppTag}
                />
                <span class='cross-span-name'>{this.crossRelationInfo.app_name}</span>
                <span class='cross-description'>{`${this.$t('所属空间：')}${this.crossRelationInfo.bk_biz_name}`}</span>
              </a>
            </div>
          </TimelineRowCell>
        ) : (
          <>
            <TimelineRowCell
              width={columnDivision}
              className='span-name-column'
            >
              <div
                class={`
            span-name-wrapper
            ${isMatchingFilter ? 'is-matching-filter' : ''}
            `}
              >
                <SpanTreeOffset
                  childrenVisible={isChildrenExpanded}
                  span={span}
                  onClick={(e: Event) => this.handleClick(e, isParent)}
                />
                <a
                  style={{ borderColor: color }}
                  class={`span-name ${isDetailExpanded ? 'is-detail-expanded' : ''}`}
                  aria-checked={isDetailExpanded}
                  role='switch'
                  tabindex={0}
                >
                  {showErrorIcon && (
                    <img
                      class='error-icon'
                      alt='error'
                      src={ErrorIcon}
                    />
                  )}
                  {span?.icon && (
                    <img
                      class='service-icon'
                      alt=''
                      src={span.icon}
                    />
                  )}
                  <span
                    class={`span-svc-name ${isParent && !isChildrenExpanded ? 'is-children-collapsed' : ''} ${
                      this.ellipsisDirection === 'rtl' ? 'is-rtl' : ''
                    }`}
                  >
                    {displayServiceName}{' '}
                    {rpc && (
                      <span>
                        <img
                          class='span-bar-row-arrow-icon'
                          alt=''
                          src={ArrowRightShapeIcon}
                        />
                        <i
                          style={{ background: rpc.color }}
                          class='span-bar-row-rpc-color-marker'
                        />
                        {rpc.serviceName}
                      </span>
                    )}
                    {noInstrumentedServer && (
                      <span>
                        <img
                          class='span-bar-row-arrow-icon'
                          alt=''
                          src={ArrowRightShapeIcon}
                        />
                        <i
                          style={{ background: noInstrumentedServer.color }}
                          class='span-bar-row-rpc-color-marker'
                        />
                        {noInstrumentedServer.serviceName}
                      </span>
                    )}
                    <small class='endpoint-name'>{rpc ? rpc.operationName : displayOperationName}</small>
                    {label && <small class='endpoint-name label'> | {label}</small>}
                  </span>
                  {groupInfo ? (
                    <Popover
                      key={isExpand}
                      v-slots={{
                        content: () =>
                          isExpand ? (
                            <span>
                              {this.$t('点击折叠')}
                              <br />
                              {this.$t('相同"Service + Span name + status"的 Span')}
                            </span>
                          ) : (
                            <span>
                              {this.$t('已折叠 {count} 个相同"Service + Span name + status"的 Span', {
                                count: groupInfo.members.length,
                              })}
                              <br />
                              {this.$t('点击展开')}
                            </span>
                          ),
                      }}
                      placement='top'
                      popoverDelay={[500, 0]}
                    >
                      {isExpand ? (
                        <i
                          class='icon-monitor icon-mc-fold-menu icon-collapsed'
                          onClick={e => this.handleToggleCollapse(e, groupInfo.id, 'collpase')}
                        ></i>
                      ) : (
                        <span
                          class='collapsed-mark'
                          onClick={e => this.handleToggleCollapse(e, groupInfo.id, 'expand')}
                        >
                          {groupInfo.members.length}
                        </span>
                      )}
                    </Popover>
                  ) : (
                    ''
                  )}
                </a>
              </div>
            </TimelineRowCell>
            <TimelineRowCell
              style={{ cursor: 'pointer' }}
              width={1 - columnDivision}
              className='span-view'
            >
              <Ticks numTicks={numTicks} />
              <Popover
                key={label}
                v-slots={{
                  content: () => (
                    <div>
                      <div>{`${this.$t('服务')}: ${displayServiceName}`}</div>
                      <div>{`${this.$t('接口')}: ${displayOperationName}`}</div>
                      {}
                      <div>{`${this.$t('类型')}: ${
                        isVirtual ? this.$t('推断') : source === 'ebpf' ? ebpfKind : SPAN_KIND_MAPS[kind]
                      }`}</div>
                      <div>{`${this.$t('耗时')}: ${formatDuration(realDuration)}`}</div>
                    </div>
                  ),
                }}
                placement='top'
                popoverDelay={[500, 0]}
              >
                <SpanBar
                  color={color}
                  hintSide={hintSide}
                  longLabel={longLabel}
                  rpc={rpc}
                  shortLabel={label}
                  span={span}
                  viewEnd={viewEnd}
                  viewStart={viewStart}
                />
              </Popover>
            </TimelineRowCell>
          </>
        )}
      </TimelineRow>
    );
  },
});
