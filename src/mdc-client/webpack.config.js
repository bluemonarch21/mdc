const webpack = require('webpack');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const { CleanWebpackPlugin } = require('clean-webpack-plugin');
const ForkTsCheckerWebpackPlugin = require('fork-ts-checker-webpack-plugin');
const path = require('path');

const entry = {
  main: path.resolve(__dirname, 'src/index.tsx'),
};

const config = {
  entry,
  module: {
    rules: [
      {
        test: /\.ts(x)?$/,
        use: {
          loader: 'ts-loader',
          options: {
            // disable type checker - we will use it in fork plugin
            transpileOnly: true,
          },
        },
      },
      {
        test: /\.css$/,
        use: [MiniCssExtractPlugin.loader, 'css-loader'],
      },
      {
        test: /\.(svg|png)$/,
        type: 'asset/resource',
      },
    ],
  },
  resolve: {
    modules: ['node_modules', 'src'],
    extensions: ['.js', '.jsx', '.tsx', '.ts'],
  },
  plugins: [
    new ForkTsCheckerWebpackPlugin(),
    new MiniCssExtractPlugin(),
    new CleanWebpackPlugin(),
    new webpack.ProvidePlugin({
      process: 'process/browser',
    }),
  ],
  optimization: {
    runtimeChunk: 'single',
    splitChunks: {
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all',
        },
      },
    },
  },
  stats: {
    warningsFilter: /export .* was not found in/,
  },
};

const common = {
  config,
  createHtmlWebpackPlugin: function (assetName) {
    return new HtmlWebpackPlugin({
      templateContent: ({ htmlWebpackPlugin }) => {
        return JSON.stringify({
          ...htmlWebpackPlugin.files,
        });
      },
      inject: false,
      filename: 'main-assets.json', // it will be in outputPath
      chunks: 'all',
    });
  },
};

module.exports = common;
