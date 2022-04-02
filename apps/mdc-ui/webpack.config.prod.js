const { merge } = require('webpack-merge');
const common = require('./webpack.config');
const path = require('path');

const outputPath = path.resolve(__dirname, 'dist');
const prodConfig = {
  output: {
    path: outputPath,
    filename: '[name]-[contenthash].js',
    publicPath: '/js/assets',
  },
  mode: 'production',
  plugins: [common.createHtmlWebpackPlugin('main')],
};

module.exports = merge(common.config, prodConfig);
