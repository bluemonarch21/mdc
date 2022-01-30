import React from 'react';

import { Link } from 'react-router-dom';
import { Upload, message, Button } from 'antd';
import { UploadProps } from 'antd/lib/upload/interface';

import mdc_robot from '../assets/mdc_robot.png';
import { UploadIcon } from '../components/';

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
  const uploadProps: UploadProps = {
    name: 'file',
    // add API to store the uploaded file
    action: 'upload',
    headers: {
      'X-CSRFToken': getCookie('csrftoken') as string,
    },
    onChange(info) {
      if (info.file.status !== 'uploading') {
        console.log(info.file, info.fileList);
      }
      if (info.file.status === 'done') {
        message.success(`${info.file.name} file uploaded successfully`);
      } else if (info.file.status === 'error') {
        message.error(`${info.file.name} file upload failed.`);
      }
    },
  };
  return (
    <div className='homePage'>
      <div>
        <img src={mdc_robot} alt='MDC Robot' className='homePage__robotImg' />
        <h1 className='homePage__header'>Music Difficulty Classifier</h1>
        <p className='homePage__message'>
          Hi. I’m the music difficulty classifier. I can tell how hard it is to play any piano pieces because I played
          them all.
        </p>
        <p className='homePage__message'>Let’s see what you’ve got!</p>
        <Upload {...uploadProps} className='homePage__upload'>
          <Button icon={<UploadIcon />} className='homePage__uploadButton'>
            UPLOAD A FILE
          </Button>
        </Upload>
        <p className='homePage__source'>a Kasetsart University B.Eng. Project・GitHub・Privacy</p>
      </div>
    </div>
  );
};

export default HomePage;
