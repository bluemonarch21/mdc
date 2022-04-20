import React, { useEffect, useState } from 'react';

import { useNavigate } from 'react-router-dom';
import { Upload, message, Button, Select } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import { UploadProps } from 'antd/lib/upload/interface';

import { FileInfo, ModelInfo } from '../api-clients/mdc';
import mdc_robot from '../assets/mdc_robot.png';
import ResultPage from './ResultPage';
import LoadingPage from './LoadingPage';

import './HomePage.scss';
import { modelsApi, predictApi } from '../api-clients';

// function getCookie(name: string): string | null {
//   let cookieValue = null;
//   if (document.cookie && document.cookie !== '') {
//     const cookies = document.cookie.split(';');
//     for (let i = 0; i < cookies.length; i++) {
//       const cookie = cookies[i].trim();
//       // Does this cookie string begin with the name we want?
//       if (cookie.substring(0, name.length + 1) === name + '=') {
//         cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
//         break;
//       }
//     }
//   }
//   return cookieValue;
// }

const HomePage: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [level, setLevel] = useState(0);
  const [model, setModel] = useState('');
  const [modelOptions, setModelOptions] = useState([] as Array<ModelInfo>);

  useEffect(() => {
    modelsApi.modelsApiV1ModelsGet().then((res) => {
      setModelOptions(res.data);
      setModel(res.data[0].id);
    });
  }, []);

  const navigate = useNavigate();
  const uploadProps: UploadProps = {
    name: 'file',
    action: 'http://127.0.0.1:8000/api/v1/files/',
    // headers: {
    //   'X-CSRFToken': getCookie('csrftoken') as string,
    // },
    onChange(info) {
      if (info.file.status !== 'uploading') {
        console.log(info.file, info.fileList);
      }
      if (info.file.status === 'uploading') {
        // navigate('./loading');
        setIsLoading(true);
      }
      if (info.file.status === 'done') {
        const uploadResponse: FileInfo = info.file.response;
        message.success(`${info.file.name} file uploaded successfully`);
        predictApi
          .predictionApiV1PredictGet(model, uploadResponse.id)
          .then((response) => {
            setLevel(response.data.label);
            setIsLoading(false);
          })
          .catch((error) => {
            if (error.response) {
              // The request was made and the server responded with a status code
              // that falls out of the range of 2xx
              if (error.response.status == 503) {
                predictApi
                  .predictionApiV1PredictGet(model, uploadResponse.id)
                  .then((response) => {
                    setLevel(response.data.label);
                    setIsLoading(false);
                  })
                  .catch((error) => {
                    console.error(error);
                  });
              }
            }
            console.error(error);
          });
        // navigate('./result');
      } else if (info.file.status === 'error') {
        message.error(`${info.file.name} file upload failed.`);
      }
    },
  };
  // const { Option } = Select;

  if (level !== 0) return <ResultPage level={level} />;
  return (
    <div className='homePage'>
      <div>
        {isLoading ? (
          <LoadingPage />
        ) : (
          <>
            <img src={mdc_robot} alt='MDC Robot' className='homePage__robotImg' />
            <h1 className='homePage__header'>Music Difficulty Classifier</h1>
            <p className='homePage__message'>
              Hi. I’m the music difficulty classifier. I can tell how hard it is to play any piano pieces because I
              played them all.
            </p>
            <p className='homePage__message'>Let’s see what you’ve got!</p>
          </>
        )}
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <select onChange={(e) => setModel(e.target.value)}>
            {modelOptions.map((o) => (
              <option key={o.id} value={o.id}>
                {o.description}
              </option>
            ))}
          </select>
        </div>
        <Upload {...uploadProps} className='homePage__upload'>
          {isLoading ? (
            <div />
          ) : (
            <Button
              icon={<UploadOutlined className='homePage__uploadIcon' style={{ fontSize: '150%' }} />}
              className='homePage__uploadButton'
            >
              <span className='homePage__uploadButtonText'>UPLOAD A FILE</span>
            </Button>
          )}
        </Upload>
        <p className='homePage__source'>a Kasetsart University B.Eng. Project・GitHub・Privacy</p>
      </div>
    </div>
  );
};

export default HomePage;
