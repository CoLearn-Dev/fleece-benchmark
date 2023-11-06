import React, { useState, useEffect, useRef } from 'react';
import {
  DashboardOutlined,
  AreaChartOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  RocketOutlined,
  LoadingOutlined,
  ClockCircleOutlined,
  SendOutlined,
  UnorderedListOutlined,
  ShareAltOutlined,
} from '@ant-design/icons';
import { List, Image, Descriptions, Breadcrumb, Layout, Menu, theme, Button, Select, Switch, Form, Input, Space, Card, Row, Col, InputNumber, Slider, notification, Typography, Modal, } from 'antd';
import type { DescriptionsProps } from 'antd';
import { Line, Gauge } from '@antv/g2plot';
import axios from 'axios';
const { TextArea, Search } = Input;
const { Option } = Select;

const { Content, Footer, Sider } = Layout;

const str_to_placeholder = (s: string, placeholder: string, mark_value: string = "null") => {
  if (s === mark_value) {
    return placeholder;
  }
  return s;
}

const App: React.FC = () => {
  const [test_id, setTestId] = useState<string>('null');
  const [test_config, setTestConfig] = useState<any>({});
  const [test_status, setTestStatus] = useState<string>('null');
  const [model, setModel] = useState<string>('null');
  const test_status_ref = useRef(test_status);
  const [stat_data, setStatData] = useState<any[]>([]);
  const stat_data_ref = useRef(stat_data);
  const [tps_his, setTpsHis] = useState<any[]>([]);
  const tps_his_ref = useRef(tps_his);
  const [reload_config, setReloadConfig] = useState<boolean>(false);
  useEffect(() => {
    stat_data_ref.current = stat_data;
  }, [stat_data]);
  useEffect(() => {
    tps_his_ref.current = tps_his;
  }, [tps_his]);
  const [tps_data, setTpsData] = useState(0.0);
  const tps_data_ref = useRef(tps_data);
  useEffect(() => {
    tps_data_ref.current = tps_data;
  }, [tps_data]);
  const icon_status: Record<string, React.ReactNode> = {
    null: <ExclamationCircleOutlined />,
    init: <RocketOutlined />,
    running: <LoadingOutlined />,
    finish: <CheckCircleOutlined />,
    error: <CloseCircleOutlined />,
    pending: <ClockCircleOutlined />,
  }
  const str_status: Record<string, string> = {
    null: "please launch a new benchmark first",
    init: "your benchmark is initializing",
    running: "your benchmark is running now",
    finish: "your benchmark is already finished",
    error: "something went error when running your benchmark",
    pending: "your benchmark will be running soon"
  }
  const get_report_title = () => {
    if (test_status !== 'finish') {
      return "your report will be available after your benchmark finished"
    } else {
      return "Benchmark Report"
    }
  }
  const [backend_url, setBackendUrl] = useState<string>('http://52.10.162.207:8000');

  const [activeBodyKey, setactiveBodyKey] = useState<string>('body1');
  const [collapsed, setCollapsed] = useState(false);
  const {
    token: { colorBgContainer },
  } = theme.useToken();

  const [api, contextHolder] = notification.useNotification();
  const [url_header, setUrlHeader] = useState<string>('http://');
  const onUrlHeaderChange = (e: any) => {
    setUrlHeader(e);
  };
  const selectBefore = (
    <Select defaultValue="http://" onChange={onUrlHeaderChange}>
      <Option value="http://">http://</Option>
      <Option value="https://">https://</Option>
    </Select>
  );
  const workload_funcs: Record<string, string> = {
    line_5s_total_180: "lambda t: int(t / 5 + 1) if t < 900 else None",
    line_10s_total_90: "lambda t: int(t / 10 + 1) if t < 900 else None",
    line_20s_total_45: "lambda t: int(t / 20 + 1) if t < 900 else None",
    single: "lambda t: t if t < 2 else None",
    custom: "",
  }
  const convert_to_pack = (values: any) => {
    var dataset_config = {}
    if (values.dataset === "arena") {
      if (!values.separate_req_in_one_visit) {
        dataset_config = {
          "separate_req_in_one_visit_with_interval": null,
        }
      } else {
        dataset_config = {
          "separate_req_in_one_visit_with_interval": values.separate_req_in_one_visit_with_interval,
        }
      }
    } else if (values.dataset === "oasst1") {
      dataset_config = {
        "separate_req_in_one_visit": values.separate_req_in_one_visit,
      }
    } else if (values.dataset === "synthesizer") {
      var func = values.func;
      if (values.func_examples !== "custom") {
        func = workload_funcs[values.func_examples]
      };
      dataset_config = {
        "func": func,
        "prompt_source": values.prompt_source,
      }
    }
    var model = values.model;
    if (values.model === "custom") {
      model = values.model_custom;
    }
    setModel(model);

    const pack = {
      "url": url_header + values.url + "/v1",
      "model": model,
      "dataset_name": values.dataset,
      "key": values.key,
      "dataset_config": dataset_config,
      "workload_range": values.workload_range,
      "kwargs": {
        "temperature": values.temperature,
        "top_p": values.top_p,
        "max_tokens": values.max_tokens,
        "skip_idle_min": 20,
        "time_step": 0.001,
        "request_timeout": 3600,
      }
    }
    console.log("send pack", pack)
    return pack
  }
  const [form_invalid, setFormInvalid] = useState<boolean>(false);

  const launch_new_benchmark = (pack: any) => {
    setTestStatus("init");
    setStatData([]);
    setTpsHis([]);
    setTpsData(0.0);
    setTestConfig(pack);
    // send request to backend
    axios.post(backend_url + '/register_and_start_test', pack).then(function (response) {
      console.log("post success", response.data);
      setTestId(response.data);
      api.success({
        message: 'Benchmark launched',
        description: 'Your benchmark has been launched, you can go to dashboard to check the status',
      });
      setactiveBodyKey("body2");
    }).catch(function (error) {
      console.log(error);
      api.error({
        message: 'Benchmark launch failed',
        description: 'Something went wrong...',
      });
    });
  }


  const onFinish = (values: any) => {
    console.log('Success:', values);
    setFormInvalid(true);
    setTestStatus("init");
    setStatData([]);
    setTpsData(0.0);
    
    // send request to backend
    const pack = convert_to_pack(values);
    launch_new_benchmark(pack);
  };

  useEffect(() => {
    test_status_ref.current = test_status;
  }, [test_status]);

  const [loading, setLoading] = useState<boolean>(false);
  useEffect(() => {
    const intervalId = setInterval(() => {
      if (test_id !== "null" && test_status_ref.current !== "finish" && test_status_ref.current !== "error") {
        if (model === "null") {
          axios.get(backend_url + "/test_model/" + test_id).then(function (response) {
            console.log("get model success", response.data);
            setModel(response.data);
          }).catch(function (error) {
            console.log(error);
          });
        }
        axios.get(backend_url + "/test_status/" + test_id).then(function (response) {
          setLoading(false);
          console.log("get status success:", response.data);
          setTestStatus(response.data);
          if (response.data === "finish") {
            api.success({
              message: 'Report available',
              description: 'Your benchmark has been finished, you can go to dashboard to check the report',
            });
          }
          if (response.data === "error") {
            axios.get(backend_url + "/error_info/" + test_id).then(function (response) {
              Modal.error({
                title: 'Benchmark running failed',
                content: 'With error: ' + response.data,
              });
            })
          }
        })
      } else {
        clearInterval(intervalId);
      }
    }, 5000);

    return () => clearInterval(intervalId);
  }, [test_id]);


  const onFinishFailed = (errorInfo: any) => {
    console.log('Failed:', errorInfo);
    // raise error
    api.error({
      message: 'Benchmark launch failed',
      description: 'Please check your input',
    });
  };

  const [data_source, setDataSource] = useState<string>("");
  const [activate_interval, setActivateInterval] = useState<boolean>(false);
  const workload_range = () => {
    if (data_source === "arena") {
      return 33000
    } else if (data_source === "oasst1") {
      return 10364
    } return 0
  }

  const [maxValue, setMaxValue] = useState(200);
  const [minValue, setMinValue] = useState(0);
  const onChangeRange = (newValue: any) => {
    setMinValue(newValue[0]);
    setMaxValue(newValue[1]);
  };

  const [current_example, setCurrentExample] = useState<string>("line_10s_total_90");

  const [report_body, setReportBody] = useState<React.ReactNode>(<div></div>);

  useEffect(() => {
    if (test_status === "finish") {
      const throughput_pic = <Image src={backend_url + "/report/throughput/" + test_id} alt="throughput" style={{ width: '100%' }} />
      const requests_status_pic = <Image src={backend_url + "/report/requests_status/" + test_id} alt="requests_status" style={{ width: '100%' }} />
      axios.get(backend_url + "/report/json/" + test_id).then(function (response) {
        const metrics = response.data;
        console.log("get metrics success", metrics);
        const metrics_items: DescriptionsProps["items"] = [
          {
            label: 'Number of Total Requests',
            children: metrics["request_num"],
          },
          {
            label: 'Fail Rate',
            children: String((parseFloat(metrics["fail_rate"]) * 100).toFixed(2)) + " %",
          },
          {
            label: 'SLO (request launched with no latency)',
            children: String((parseFloat(metrics["SLO"]) * 100).toFixed(2)) + " %",
          },
          {
            label: 'Max Throughput / tokens per second',
            children: parseFloat(metrics["Throughput"]).toFixed(2),
          },
          {
            label: 'Time To First Token (avg)/ ms',
            children: (parseFloat(metrics.TTFT.avg) * 1000).toFixed(2),
          },
          {
            label: 'Time Per Output Token (avg) /ms',
            children: (parseFloat(metrics.TPOT.avg) * 1000).toFixed(2),
          },
        ]
        var config_metrics_items: DescriptionsProps["items"] = []
        for (const [key, value] of Object.entries(test_config)) {
          if (key === "kwargs" || key === "dataset_config") {
            for (const [key2, value2] of Object.entries(value as {[key: string]: any})) {
              config_metrics_items.push({
                label: key+":"+key2,
                children: String(value2),
              })
            }
          } else {
            config_metrics_items.push({
              label: key,
              children: String(value),
            })
          }
        }
        console.log(metrics_items)
        setReportBody(
          <Space direction="vertical" style={{ display: 'flex' }}>
            <Card title="Metrics">
              <Descriptions bordered items={metrics_items} />
            </Card>
            <Space>
              <Card title="Throughput">
                {throughput_pic}
              </Card>
              <Card title="Requests Status">
                {requests_status_pic}
              </Card>
            </Space>
            <Card title="Config">
              <Space direction="vertical">
                <Descriptions bordered items={config_metrics_items} />
                <Button type="dashed" block onClick={(e: any)=>{launch_new_benchmark(test_config)}}>
                  launch a new benchmark with this config
                </Button>
              </Space>
            </Card>
          </Space>
        )
      }).catch(function (error) {
        console.log(error);
      });
    } else {
      setReportBody(<div></div>)
    }
  }, [test_status, reload_config]);

  const [line_graph, setLineGraph] = useState<null | Line>(null);
  const line_graph_ref = useRef(line_graph);
  const [tps_gauge, setTpsGauge] = useState<null | Gauge>(null);
  const tps_gauge_ref = useRef(tps_gauge);
  const [gauge_max, setGaugeMax] = useState<number>(30);
  const gauge_max_ref = useRef(gauge_max);
  const [line_tps, setLineTps] = useState<null | Line>(null);
  const line_tps_ref = useRef(line_tps);
  useEffect(() => {
    line_tps_ref.current = line_tps;
  }, [line_tps]);
  useEffect(() => {
    gauge_max_ref.current = gauge_max;
  }, [gauge_max]);
  useEffect(() => {
    tps_gauge_ref.current = tps_gauge;
  }, [tps_gauge]);
  useEffect(() => {
    line_graph_ref.current = line_graph;
  }, [line_graph]);
  useEffect(() => {
    const IntervalId = setInterval(() => {
      if (test_id !== "null" && test_status_ref.current === "running") {
        axios.get(backend_url + "/trace/status/" + test_id).then(function (response) {
          setStatData(prev => [...prev, ...response.data]);
          // if (stat_data_ref.current.length > 100) {
          //   setStatData(prev => prev.slice(1));
          // }
          // console.log(stat_data_ref.current);
        }).catch(function (error) {
          console.log(error);
        })
        axios.get(backend_url + "/trace/tps/" + test_id + "?model=" + model).then(function (response) {
          setTpsData(parseFloat(response.data['tps']));
          setTpsHis(prev => [...prev, response.data]);
          // console.log(tps_data_ref.current);
        }).catch(function (error) {
          console.log(error);
        })
        if (line_graph_ref.current === null) {
          const line = new Line('req_stat_graph', {
            data: stat_data_ref.current,
            xField: 'timestamp',
            yField: 'number',
            seriesField: 'status',
            legend: {
              position: 'top',
            },
            smooth: true,
            area: {
              style: {
                fillOpacity: 0.15,
              },
            },
            animation: {
              appear: {
                animation: 'wave-in',
                duration: 3000,
              },
            },
          });
          line.render();
          setLineGraph(line);
        } else {
          line_graph_ref.current.changeData(stat_data_ref.current);
        }
        if (tps_gauge_ref.current === null) {
          const gauge = new Gauge('tps_gauge', {
            percent: 0,
            radius: 0.75,
            range: {
              color: '#30BF78',
              width: 12,
            },
            indicator: {
              pointer: {
                style: {
                  stroke: '#D0D0D0',
                },
              },
              pin: {
                style: {
                  stroke: '#D0D0D0',
                },
              },
            },
            gaugeStyle: {
              lineCap: 'round',
            },
            axis: {
              label: {
                formatter(v) {
                  return Number(v) * gauge_max_ref.current;
                },
              },
            },
            statistic: {
              content: {
                formatter: () => `TPS: ${tps_data_ref.current}`,
                style: {
                  color: 'rgba(0,0,0,0.65)',
                },
              },
            },
          });
          gauge.render();
          setTpsGauge(gauge);
        }else{
          if (tps_data_ref.current > gauge_max_ref.current) {
            setGaugeMax(Math.ceil(tps_data_ref.current / 10) * 10);
          }else if (tps_data_ref.current < gauge_max_ref.current / 2 && gauge_max_ref.current > 30){
            setGaugeMax(30);
          }
          tps_gauge_ref.current.update({
            axis: {
              label: {
                formatter(v) {
                  return Number(v) * gauge_max_ref.current;
                },
              },
            },
          });
          tps_gauge_ref.current.changeData(tps_data_ref.current / gauge_max_ref.current);
        }
        if (line_tps_ref.current === null) {
          // TODO
          const line = new Line('tps_graph', {
            data: tps_his_ref.current,
            xField: 'timestamp',
            yField: 'tps',
            legend: {
              position: 'top',
            },
            smooth: true,
            animation: {
              appear: {
                // animation: 'wave-in',
                duration: 3000,
              },
            },
          });
          line.render();
          setLineTps(line);
        } else {
          line_tps_ref.current.changeData(tps_his_ref.current);
        }
      } else {
        clearInterval(IntervalId);
      }
    }, 1000);
    return () => clearInterval(IntervalId);
  }, [test_status, reload_config]);

  const [set_dashboard_id, setSetDashboardId] = useState<string>("null");
  useEffect(() => {
    setSetDashboardId(test_id);
  }, [test_id]);

  useEffect(() => {
    if (reload_config){
      setReloadConfig(false);
      setTestStatus("null");
      axios.get(backend_url + "/config/" + test_id).then(function (response) {
        console.log("get config success", response.data);
        const config = response.data;
        setModel(config["model"]);
        setTestConfig(config);
        console.log("config", config);
      }).catch(function (error) {
        console.log(error);
      });
    }
  }, [reload_config]);

  const id_to_show = (id: string) => {
    if (id === "null") {
      return "";
    }else{
      return id;
    }
  }

  const [costum_model, setCustomModel] = useState<boolean>(false);
  const [form_temp, setFormTemp] = useState(0.7);
  const [form_top_p, setFormTopP] = useState(1.0);
  const [form_max_tokens, setFormMaxTokens] = useState(1024);
  const [id_list, setIdList] = useState<string[]>([]);
  useEffect(() => {
    if (activeBodyKey==="body3"){
      axios.get(backend_url + "/id_list").then(function (response) {
        console.log("get id list success", response.data);
        setIdList(response.data);
    }).catch(function (error) {
      console.log(error);
    });
  }}, [activeBodyKey]);
  const [input_backend_url, setInputBackendUrl] = useState<string>('52.10.162.207:8000');

  return (
    <>
      {contextHolder}
      <Layout style={{ minHeight: '100vh' }}>
        <Sider collapsible collapsed={collapsed} onCollapse={(value) => setCollapsed(value)}>
          <div className="demo-logo-vertical" />
          <Menu theme="dark" mode="inline" selectedKeys={[activeBodyKey]}>
            <Menu.Item key="body1" icon={<DashboardOutlined />} onClick={(e: any) => { setactiveBodyKey(e.key); }}>
              Launch new
            </Menu.Item>
            <Menu.Item key="body2" icon={<AreaChartOutlined />} onClick={(e: any) => { setactiveBodyKey(e.key); }}>
              Report
            </Menu.Item>
            <Menu.Item key="body3" icon={<UnorderedListOutlined />} onClick={(e: any) => { setactiveBodyKey(e.key); }}>
              All tests
            </Menu.Item>
          </Menu>

        </Sider>
        <Layout>
          <Content style={{ margin: '0 16px' }}>
            <div hidden={test_id==="null"}>
              <Breadcrumb style={{ margin: '16px 0' }}>
                <Breadcrumb.Item>Testcase</Breadcrumb.Item>
                <Breadcrumb.Item>{test_id}</Breadcrumb.Item>
                <Breadcrumb.Item>{str_to_placeholder(test_status,"loading")}</Breadcrumb.Item>
              </Breadcrumb>
            </div>
            <div style={{ padding: 24, minHeight: 360, background: colorBgContainer }}>
              <div hidden={activeBodyKey !== "body1"}>
                <Space direction="vertical" size="middle" style={{ display: 'flex' }}>
                  <Card title="Benchmark backend url">
                    <Space.Compact style={{ width: '100%' }} size="large">
                      <Input addonBefore="http://" 
                        value={input_backend_url} 
                        onChange={(e: any)=>{setInputBackendUrl(e)}}
                        placeholder="input the url of benchmark endpoint" 
                        onPressEnter={(e)=>(setBackendUrl('http://'+input_backend_url))}/>
                      <Button type="primary" onClick={(e)=>(setBackendUrl('http://'+input_backend_url))}>Set</Button>
                    </Space.Compact>
                  </Card>
                  <Card
                    style={{ width: '100%' }}
                    title="Config your benchmark test"
                  >
                    <Form
                      name="basic"
                      // labelCol={{ span: 8 }}
                      // wrapperCol={{ span: 16 }}
                      // style={{ maxWidth: 600 }}
                      layout="vertical"
                      initialValues={{ remember: true }}
                      onFinish={onFinish}
                      onFinishFailed={onFinishFailed}
                      autoComplete="off"
                      disabled={form_invalid}
                    >
                      {/* <Form.Item
                        label="benchmark backend url"
                        name="benchmark_backend_url"
                        initialValue="52.10.162.207:8000"
                      >
                        <Input addonBefore="http://"/>
                      </Form.Item> */}
                      <Form.Item
                        label="endpoint url"
                        name="url"
                        rules={[{ required: true, message: 'Please input your endpoint url!' }]}
                      >
                        <Input addonBefore={selectBefore} addonAfter="/v1" />
                      </Form.Item>

                      <Form.Item
                        label="api key"
                        name="key"
                        initialValue="EMPTY"
                      >
                        <Input />
                      </Form.Item>
                      <Form.Item
                        label="model"
                        name="model"
                        initialValue="llama-2-7b-chat"
                      >
                        <Select defaultValue={"llama-2-7b-chat"} onChange={(e: any) => { if (e==='custom'){setCustomModel(true);}else{setCustomModel(false);} }}>
                          <Select.Option value="llama-2-7b-chat">llama-2-7b-chat</Select.Option>
                          <Select.Option value="llama-2-70b-chat">llama-2-70b-chat</Select.Option>
                          <Select.Option value="Llama-2-7b-chat-hf">Llama-2-7b-chat-hf</Select.Option>
                          <Select.Option value="gpt-3.5-turbo">gpt-3.5-turbo</Select.Option>
                          <Select.Option value="gpt-4">gpt-4</Select.Option>
                          <Select.Option value="custom">custom</Select.Option>
                        </Select>
                      </Form.Item>
                      <Form.Item
                        label="model"
                        name="model_custom"
                        hidden={!costum_model}
                      >
                        <Input />
                      </Form.Item>
                      <Form.Item
                        label="dataset"
                        name="dataset"
                        rules={[{ required: true, message: 'Please choose one dataset' }]}
                      >
                        <Select onChange={(e: any) => { setDataSource(e); }}>
                          <Select.Option value="arena">chatbot-arena</Select.Option>
                          <Select.Option value="oasst1">oasst1</Select.Option>
                          <Select.Option value="synthesizer">synthesize now</Select.Option>
                        </Select>
                      </Form.Item>
                      <Form.Item
                        label="prompt source"
                        name="prompt_source"
                        hidden={data_source !== "synthesizer"}
                      >
                        <Select>
                          <Select.Option value="arena">chatbot-arena</Select.Option>
                          <Select.Option value="oasst1">oasst1</Select.Option>
                        </Select>
                      </Form.Item>
                      <Form.Item
                        label="separate requests in one visit"
                        name="separate_req_in_one_visit"
                        initialValue={false}
                        hidden={!(data_source === "oasst1" || data_source === "arena")}
                      >
                        <Switch onChange={(e: any) => { setActivateInterval(e) }} />
                      </Form.Item>
                      <Form.Item
                        label="interval when separate"
                        name="separate_req_in_one_visit_with_interval"
                        initialValue={10}
                        hidden={data_source !== "arena" || !activate_interval}
                      >
                        <InputNumber addonAfter='s' />
                      </Form.Item>
                      <Form.Item
                        label="workload function examples"
                        name="func_examples"
                        initialValue={"line_10s_total_90"}
                        hidden={data_source !== "synthesizer"}
                      >
                        <Select onChange={(e: any) => { setCurrentExample(e); }}>
                          <Select.Option value="line_5s_total_180">launch a request for each 5s, total 180 requests</Select.Option>
                          <Select.Option value="line_10s_total_90">launch a request for each 10s, total 90 requests</Select.Option>
                          <Select.Option value="line_20s_total_45">launch a request for each 20s, total 45 requests</Select.Option>
                          <Select.Option value="single">launch a single request</Select.Option>
                          <Select.Option value="custom">custom</Select.Option>
                        </Select>
                      </Form.Item>
                      <Form.Item
                        label="workload function"
                        name="func"
                        hidden={(data_source !== "synthesizer" || current_example === "custom")}
                      >
                        <Typography.Text className="ant-form-text" type="secondary">{workload_funcs[current_example]}</Typography.Text>
                      </Form.Item>
                      <Form.Item
                        label="workload function"
                        name="func"
                        hidden={(data_source !== "synthesizer" || current_example !== "custom")}
                      >
                        <TextArea rows={4} />
                      </Form.Item>
                      <Form.Item
                        label="sample range"
                        name="workload_range"
                        initialValue={[0, 200]}
                        hidden={!(data_source === "oasst1" || data_source === "arena")}
                      >
                        <Row>
                          <Col span={20}>
                            <Slider range={{ draggableTrack: true }} min={0} max={workload_range()} onChange={onChangeRange} value={[minValue, maxValue]} />
                          </Col>
                          <Col span={2}>
                            <InputNumber
                              min={0}
                              max={workload_range()}
                              // style={{ margin: '0 16px' }}
                              value={minValue}
                              onChange={(e: any) => { setMinValue(e) }}
                            />
                          </Col>
                          <Col span={2}>
                            <InputNumber
                              min={0}
                              max={workload_range()}
                              // style={{ margin: '0 16px' }}
                              value={maxValue}
                              onChange={(e: any) => { setMaxValue(e) }}
                            />
                          </Col>
                        </Row>
                      </Form.Item>
                      <Form.Item
                        label="temperature"
                        name="temperature"
                        initialValue={0.7}
                      >
                        <Row justify="space-between">
                          <Col span={21}>
                            <Slider min={0} max={1.0} step={0.1} onChange={setFormTemp} value={form_temp}/>
                          </Col>
                          <Col span={2}>
                            <InputNumber
                              min={0}
                              max={1.0}
                              value={form_temp}
                              step={0.1}
                              onChange={(e: any) => { setFormTemp(e.toFixed(1)) }}
                            />
                          </Col>
                        </Row>
                        
                      </Form.Item>
                      <Form.Item
                        label="top p"
                        name="top_p"
                        initialValue={1.0}
                      >
                        <Row  justify="space-between">
                          <Col span={21}>
                            <Slider min={0} max={1.0} step={0.1} onChange={setFormTopP} value={form_top_p}/>
                          </Col>
                          <Col span={2}>
                            <InputNumber
                              min={0}
                              max={1.0}
                              value={form_top_p}
                              step={0.1}
                              onChange={(e: any) => { setFormTopP(e.toFixed(1)) }}
                            />
                          </Col>
                        </Row>
                      </Form.Item>
                      <Form.Item
                        label="max output tokens"
                        name="max_tokens"
                        initialValue={1024}
                      >
                        <Row  justify="space-between">
                          <Col span={21}>
                            <Slider min={0} max={4096} step={1} onChange={setFormMaxTokens} value={form_max_tokens}/>
                          </Col>
                          <Col span={2}>
                            <InputNumber
                              min={0}
                              max={4096}
                              value={form_max_tokens}
                              step={1}
                              onChange={(e: any) => { setFormMaxTokens(e) }}
                              
                            />
                          </Col>
                        </Row>
                      </Form.Item>
                      <Form.Item>
                        <Button block type="primary" htmlType="submit">
                          Launch new benchmark
                        </Button>
                      </Form.Item>
                    </Form>
                  </Card>
                  <Button type="dashed" disabled={!form_invalid} block onClick={(e: any) => { setFormInvalid(false); }}>
                    activate config panel
                  </Button>
                </Space>
              </div>
              <div hidden={activeBodyKey !== "body2"}>
                <Space direction="vertical" size="middle" style={{ display: 'flex' }}>
                  <Card title="Task to monitor">
                    <Space.Compact style={{ width: '100%' }} size="large">
                      <Input prefix={<SendOutlined />} value={id_to_show(set_dashboard_id)} placeholder="input the id of the task you want to monitor" 
                        onChange={(e: any) => { setSetDashboardId(e.target.value) }}
                        onPressEnter={(e: any) => { setTestId(e.target.value); setLoading(true); setReloadConfig(true);}}/>
                      <Button type="primary" loading={loading} onClick={(e: any) => { setTestId(set_dashboard_id); setLoading(true); setReloadConfig(true);}}>Load</Button>
                    </Space.Compact>
                  </Card>
                    <Card
                      hidden={test_status !== "running"}
                      title={<Space>
                        <span>{icon_status[test_status]}</span>
                        <span>{str_status[test_status]}</span>
                      </Space>}
                      extra={'status: ' + test_status}>
                        <Space direction="vertical" style={{ display: 'flex' }}>
                          <Card title="TPS">
                            <Row>
                              <Col span={8}><div id="tps_gauge"></div></Col>
                              <Col span={16}><div id="tps_graph"></div></Col>
                            </Row>
                          </Card>
                          <Card title="Requests Status">
                            <div id="req_stat_graph"></div>
                          </Card>
                        </Space>
                    </Card>
                  <Card title={get_report_title()} hidden={test_status !== "finish"}>
                    {report_body}
                  </Card>
                </Space>
              </div>
              <div hidden={activeBodyKey !== "body3"}>
                <Card title="History Tests">
                <List
                itemLayout="horizontal"
                dataSource={id_list}
                pagination={
                  {
                    pageSize: 10,
                    position: 'bottom',
                    align: 'center',
                  }
                }
                renderItem={(item, index) => (
                  <List.Item>
                    <List.Item.Meta
                      title={<>{index}. <a onClick={(e: any)=>{
                        setTestId(item[0]); setLoading(true); setReloadConfig(true); setactiveBodyKey("body2"); 
                      }}>ID: {item}</a></>}
                      description={"launch time: "+item[1]}
                    />
                  </List.Item>
                )}
              />
                </Card>
              </div>
            </div>
          </Content>
          <Footer style={{ textAlign: 'center' }}>fleece benchmark ©2023</Footer>
        </Layout>
      </Layout>
    </>
  );
};

export default App;