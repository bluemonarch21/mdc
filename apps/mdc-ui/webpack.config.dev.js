const path = require('path');

const { merge } = require('webpack-merge');
const common = require('./webpack.config');
const HtmlWebpackPlugin = require("html-webpack-plugin");
const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin;

// const outputPath = path.resolve(__dirname, './dist');
// const outputPath = path.resolve(__dirname, '../mdc-django/core/static');

const devConfig = {
  // output: {
  //   path: outputPath,
  //   filename: '[name].js',
  //   publicPath: '/static/',
  //   assetModuleFilename: 'img/[hash][ext][query]',
  // },
  mode: 'development',
  devServer: {
    writeToDisk: true,
    hot: true,
  },
  devtool: 'eval-source-map',
  plugins: [
    new HtmlWebpackPlugin({
      title: 'Music Difficulty Classifier',
      template: path.resolve(__dirname, 'public/index.html'),
      hash: true,
      appMountId: 'root',
    }),
    new BundleAnalyzerPlugin({
      analyzerMode: 'static',
      openAnalyzer: false,
    }),
  ],
};

module.exports = merge(common.config, devConfig);
