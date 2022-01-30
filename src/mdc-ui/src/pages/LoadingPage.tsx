import React from 'react';

import { Button } from 'antd';
import { ShareAltOutlined } from '@ant-design/icons';
import Texty from 'rc-texty';
import 'rc-texty/assets/index.css';

import mdc_piano2 from '../assets/mdc_piano2.png';

import './LoadingPage.scss';

const LoadingPage: React.FC = () => {
  return (
    <div className='loadingPage'>
      <div>
        <img src={mdc_piano2} alt='MDC Piano' className='loadingPage__pianoImg' />
        <div className='texty-demo loadingPage__antMotion' style={{ marginTop: 64 }}>
          <Texty>Let me work on it.</Texty>
        </div>
        <p className='loadingPage__source'>a Kasetsart University B.Eng. Project・GitHub・Privacy</p>
      </div>
    </div>
  );
};

export default LoadingPage;
