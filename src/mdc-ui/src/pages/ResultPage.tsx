import React from 'react';

import { Button } from 'antd';
import { ShareAltOutlined } from '@ant-design/icons';

import mdc_robot from '../assets/mdc_robot.png';
import mdc_piano from '../assets/mdc_piano.png';
import mdc_sheet from '../assets/mdc_sheet.png';

import './ResultPage.scss';

const ResultPage: React.FC = () => {
  return (
    <div className='resultPage'>
      <div>
        <p className='resultPage__message'>Your song is</p>
        <h1 className='resultPage__header'>Level 7 (Difficult)</h1>
        <h3 className='resultPage__henle'>on the Henle scale</h3>
        <p className='resultPage__analysis'>according to my analysis.</p>
        <img src={mdc_piano} alt='MDC Piano' className='resultPage__pianoImg' />
        <img src={mdc_robot} alt='MDC Robot' className='resultPage__robotImg' />
        <img src={mdc_sheet} alt='MDC Music Sheet' className='resultPage__sheetImg' />
        <Button
          className='resultPage__shareButton'
          icon={<ShareAltOutlined className='resultPage__shareIcon' style={{ fontSize: '150%' }} />}
        >
          <span className='resultPage__shareButtonText'>SHARE</span>
        </Button>
        <Button type='link' href='./' className='resultPage__returnButton'>
          CHECK ANOTHER SONG
        </Button>
        <p className='resultPage__source'>a Kasetsart University B.Eng. Project・GitHub・Privacy</p>
      </div>
    </div>
  );
};

export default ResultPage;
