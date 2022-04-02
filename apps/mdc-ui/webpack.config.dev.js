const path = require('path');

const {merge} = require('webpack-merge');
const common = require('./webpack.config');
const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin;

// const outputPath = path.resolve(__dirname, './dist');
const outputPath = path.resolve(__dirname, '../mdc-django/core/static');

const devConfig = {
  output: {
    path: outputPath,
    filename: '[name].js',
    publicPath: '/static/',
    assetModuleFilename: 'img/[hash][ext][query]',
  },
  mode: 'development',
  devServer: {
    writeToDisk: true,
    hot: true,
  },
  devtool: 'eval-source-map',
  plugins: [
    common.createHtmlWebpackPlugin('main'),
    new BundleAnalyzerPlugin({
      analyzerMode: 'static',
      openAnalyzer: false,
    }),
  ],
};

module.exports = merge(common.config, devConfig);
