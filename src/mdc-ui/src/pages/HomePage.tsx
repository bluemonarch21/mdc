import React, { useState } from 'react';

import { useNavigate } from 'react-router-dom';
import { Upload, message, Button } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import { UploadProps } from 'antd/lib/upload/interface';

import mdc_robot from '../assets/mdc_robot.png';
import ResultPage from './ResultPage';
import LoadingPage from './LoadingPage';

import './HomePage.scss';

function getCookie(name: string): string | null {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) === name + '=') {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

const HomePage: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [level, setLevel] = useState(0);
  const navigate = useNavigate();
  const uploadProps: UploadProps = {
    name: 'file',
    action: 'upload',
    headers: {
      'X-CSRFToken': getCookie('csrftoken') as string,
    },
    onChange(info) {
      if (info.file.status !== 'uploading') {
        console.log(info.file, info.fileList);
      }
      if (info.file.status === 'uploading') {
        // navigate('./loading');
        setIsLoading(true);
      }
      if (info.file.status === 'done') {
        setLevel(info.file.response);
        setIsLoading(false);
        message.success(`${info.file.name} file uploaded successfully`);
        // navigate('./result');
      } else if (info.file.status === 'error') {
        message.error(`${info.file.name} file upload failed.`);
      }
    },
  };
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
