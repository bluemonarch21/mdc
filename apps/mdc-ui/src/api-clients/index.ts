import axios from 'axios';

import { ModelsApi, FilesApi, PredictApi } from './mdc';

export const axiosInstance = axios.create({
  baseURL: process.env.NODE_ENV === 'development' ? 'http://localhost:8000/' : 'https://my.production.site.com/',
});

const modelsApi = new ModelsApi(undefined, '', axiosInstance);
const filesApi = new FilesApi(undefined, '', axiosInstance);
const predictApi = new PredictApi(undefined, '', axiosInstance);

export { modelsApi, filesApi, predictApi };
