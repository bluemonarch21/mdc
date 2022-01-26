import React from 'react';

import { Link } from 'react-router-dom';
import { Upload, message, Button } from 'antd';
import { UploadOutlined } from '@ant-design/icons';

const HomePage: React.FC = () => {
  const uploadProps = {
    name: 'file',
    // add API to store the uploaded file
    action: 'https://www.mocky.io/v2/5cc8019d300000980a055e76',
    headers: {
      authorization: 'authorization-text',
    },
    onChange(info: any) {
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
    <div>
      <Upload {...uploadProps}>
        <Button icon={<UploadOutlined />}>Click to Upload</Button>
      </Upload>,
    </div>
  );
};

export default HomePage;
