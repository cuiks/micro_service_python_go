package api

import (
	"context"
	"fmt"
	"github.com/gin-gonic/gin"
	"github.com/go-redis/redis/v8"
	"go.uber.org/zap"
	"mxshop-api/user-web/forms"
	"mxshop-api/user-web/global"
	"net/http"
	"time"
)

func SendSms(ctx *gin.Context) {
	smsForm := forms.SmsForm{}
	if err := ctx.ShouldBindJSON(&smsForm); err != nil {
		HandleValidatorError(ctx, err)
		return
	}
	rdb := redis.NewClient(&redis.Options{
		Addr: fmt.Sprintf("%s:%d", global.ServerConfig.RedisConfig.Host, global.ServerConfig.RedisConfig.Port),
	})
	err := rdb.Set(
		context.Background(),
		smsForm.Mobile,
		smsForm.Mobile,
		time.Duration(global.ServerConfig.RedisConfig.Ex)*time.Second,
	).Err()
	if err != nil {
		zap.S().Errorw("[sms]Redis缓存失败：", "msg", err.Error())
		ctx.JSON(http.StatusInternalServerError, gin.H{
			"msg": "验证码Redis缓存失败!",
		})
		return
	}
	ctx.JSON(http.StatusOK, gin.H{
		"msg": "发送成功",
	})
	return
}
