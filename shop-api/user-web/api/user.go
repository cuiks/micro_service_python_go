package api

import (
	"context"
	"fmt"
	"github.com/dgrijalva/jwt-go"
	"github.com/gin-gonic/gin"
	"github.com/go-playground/validator/v10"
	"github.com/go-redis/redis/v8"
	"go.uber.org/zap"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"mxshop-api/user-web/forms"
	"mxshop-api/user-web/global"
	"mxshop-api/user-web/global/response"
	"mxshop-api/user-web/middlewares"
	"mxshop-api/user-web/models"
	"mxshop-api/user-web/proto"
	"net/http"
	"strconv"
	"strings"
	"time"
)

func RemoveTopStruct(fileds map[string]string) map[string]string {
	rsp := map[string]string{}
	for field, err := range fileds {
		rsp[field[strings.Index(field, ".")+1:]] = err
	}
	return rsp
}

func HandleGrpcErrorToHttp(err error, c *gin.Context) {
	// 将grpc的code转换成http状态码
	if err != nil {
		if e, ok := status.FromError(err); ok {
			switch e.Code() {
			case codes.NotFound:
				c.JSON(http.StatusNotFound, gin.H{
					"msg": e.Message(),
				})
			case codes.Internal:
				c.JSON(http.StatusInternalServerError, gin.H{
					"msg": "internal error",
				})
			case codes.InvalidArgument:
				c.JSON(http.StatusBadRequest, gin.H{
					"msg": "params error",
				})
			case codes.Unavailable:
				c.JSON(http.StatusInternalServerError, gin.H{
					"msg": "用户服务不可用",
				})
			case codes.AlreadyExists:
				c.JSON(http.StatusBadRequest, gin.H{
					"msg": "用户已存在",
				})
			default:
				c.JSON(http.StatusInternalServerError, gin.H{
					"msg": e.Code(),
				})
			}
			return
		}
	}
}

func HandleValidatorError(c *gin.Context, err error) {
	errs, ok := err.(validator.ValidationErrors)
	if !ok {
		c.JSON(http.StatusOK, gin.H{
			"msg": err.Error(),
		})
		return
	}
	c.JSON(http.StatusBadRequest, gin.H{
		"error": RemoveTopStruct(errs.Translate(global.Trans)),
	})
	return
}

func GetUserList(ctx *gin.Context) {
	claims, _ := ctx.Get("claims")
	currentUser := claims.(*models.CustomClaims)
	zap.S().Infof("访问用户：%d", currentUser.ID)

	pn := ctx.DefaultQuery("pn", "0")
	pnInt, _ := strconv.Atoi(pn)
	pSize := ctx.DefaultQuery("psize", "10")
	pSizeInt, _ := strconv.Atoi(pSize)
	rsp, err := global.UserSrvClient.GetUserList(context.Background(), &proto.PageInfo{
		Pn:    uint32(pnInt),
		PSize: uint32(pSizeInt),
	})
	if err != nil {
		zap.S().Errorw("[GetUserList] 查询 [用户列表]失败")
		HandleGrpcErrorToHttp(err, ctx)
		return
	}

	result := make([]interface{}, 0)
	for _, value := range rsp.Data {

		data := response.UserResponse{
			Id:       value.Id,
			NickName: value.NickName,
			//Birthday: time.Time(time.Unix(int64(value.BirthDay), 0)).Format("2006-01-02"),
			Birthday: response.JsonTime(time.Unix(int64(value.BirthDay), 0)),
			Gender:   value.Gender,
			Mobile:   value.Mobile,
		}
		//data := make(map[string]interface{})
		//data["id"] = value.Id
		//data["name"] = value.NickName
		//data["birthday"] = value.BirthDay
		//data["gender"] = value.Gender
		//data["mobile"] = value.Mobile

		result = append(result, data)
	}
	ctx.JSON(http.StatusOK, result)
	return
}

func PassWordLogin(c *gin.Context) {
	passWordLoginForm := forms.PassWordLoginForm{}
	if err := c.ShouldBind(&passWordLoginForm); err != nil {
		HandleValidatorError(c, err)
		return
	}

	//if !store.Verify(passWordLoginForm.CaptchaId, passWordLoginForm.Captcha, false) {
	//	c.JSON(http.StatusBadRequest, gin.H{
	//		"captcha": "验证码错误",
	//	})
	//	return
	//}

	// 登录的逻辑
	if rsp, err := global.UserSrvClient.GetUserByMobile(context.Background(), &proto.MobileRequest{
		Mobile: passWordLoginForm.Mobile,
	}); err != nil {
		if e, ok := status.FromError(err); ok {
			switch e.Code() {
			case codes.NotFound:
				c.JSON(http.StatusBadRequest, map[string]string{
					"mobile": "用户不存在",
				})
			default:
				c.JSON(http.StatusInternalServerError, map[string]string{
					"mobile": "登录失败",
				})
			}
			return
		}
	} else {
		// 检查密码
		if passRsp, passErr := global.UserSrvClient.CheckPassWord(context.Background(), &proto.PasswordCheckInfo{
			Password:          passWordLoginForm.PassWord,
			EncryptedPassword: rsp.PassWord,
		}); passErr != nil {
			c.JSON(http.StatusInternalServerError, map[string]string{
				"msg": "登录失败",
			})
		} else {
			if passRsp.Success {
				// 生成token
				j := middlewares.NewJWT()
				claims := models.CustomClaims{
					ID:          uint(rsp.Id),
					NickName:    rsp.NickName,
					AuthorityId: uint(rsp.Role),
					StandardClaims: jwt.StandardClaims{
						ExpiresAt: time.Now().Unix() + 60*60*24*30, // 30天过期
						Issuer:    "imooc",
						NotBefore: time.Now().Unix(), // 签名的生效时间
					},
				}
				token, err := j.CreateToken(claims)
				if err != nil {
					zap.S().Errorw("[PassWordLogin] 生成token失败", "msg", err.Error())
					c.JSON(http.StatusInternalServerError, gin.H{
						"msg": "生成token失败",
					})
					return
				}

				c.JSON(http.StatusOK, gin.H{
					"id":         rsp.Id,
					"nick_name":  rsp.NickName,
					"token":      token,
					"expired_at": (time.Now().Unix() + 60*60*24*30) * 1000,
				})
			} else {
				c.JSON(http.StatusOK, map[string]string{
					"msg": "密码错误",
				})
			}

		}
	}
	return
}

func Register(ctx *gin.Context) {
	registerForm := forms.RegisterForm{}
	if err := ctx.ShouldBind(&registerForm); err != nil {
		HandleValidatorError(ctx, err)
		return
	}
	// 验证code
	rdb := redis.NewClient(&redis.Options{
		Addr: fmt.Sprintf("%s:%d", global.ServerConfig.RedisConfig.Host, global.ServerConfig.RedisConfig.Port),
	})
	if redisResult, err := rdb.Get(context.Background(), registerForm.Mobile).Result(); err == redis.Nil {
		ctx.JSON(http.StatusBadRequest, gin.H{
			"msg": "验证码错误",
		})
		return
	} else {
		if redisResult != registerForm.Code {
			ctx.JSON(http.StatusBadRequest, gin.H{
				"msg": "验证码错误",
			})
			return
		}
	}
	// 判断用户是否已注册

	rsp, err := global.UserSrvClient.CreateUser(context.Background(), &proto.CreateUserInfo{
		NickName: registerForm.Mobile,
		PassWord: registerForm.PassWord,
		Mobile:   registerForm.Mobile,
	})
	if err != nil {
		HandleGrpcErrorToHttp(err, ctx)
		return
	}

	j := middlewares.NewJWT()
	claims := models.CustomClaims{
		ID:          uint(rsp.Id),
		NickName:    rsp.NickName,
		AuthorityId: uint(rsp.Role),
		StandardClaims: jwt.StandardClaims{
			ExpiresAt: time.Now().Unix() + 60*60*24*30, // 30天过期
			Issuer:    "imooc",
			NotBefore: time.Now().Unix(), // 签名的生效时间
		},
	}
	token, err := j.CreateToken(claims)
	if err != nil {
		zap.S().Errorw("[Register] 生成token失败", "msg", err.Error())
		ctx.JSON(http.StatusInternalServerError, gin.H{
			"msg": "生成token失败",
		})
		return
	}

	ctx.JSON(http.StatusOK, gin.H{
		"id":         rsp.Id,
		"nick_name":  rsp.NickName,
		"token":      token,
		"expired_at": (time.Now().Unix() + 60*60*24*30) * 1000,
	})

}

func GetUserDetail(ctx *gin.Context) {
	claims, _ := ctx.Get("claims")
	currentUser := claims.(*models.CustomClaims)
	zap.S().Infof("访问用户: %d", currentUser.ID)

	rsp, err := global.UserSrvClient.GetUserById(context.Background(), &proto.IdRequest{
		Id: int32(currentUser.ID),
	})
	if err != nil {
		HandleGrpcErrorToHttp(err, ctx)
		return
	}
	ctx.JSON(http.StatusOK, gin.H{
		"name":     rsp.NickName,
		"birthday": time.Unix(int64(rsp.BirthDay), 0).Format("2006-01-12"),
		"gender":   rsp.Gender,
		"mobile":   rsp.Mobile,
	})
}

func UpdateUser(ctx *gin.Context) {
	UpdateUserForm := forms.UpdateUserForm{}
	claims, _ := ctx.Get("claims")
	currentUser := claims.(*models.CustomClaims)
	zap.S().Infof("访问用户: %d", currentUser.ID)

	loc, _ := time.LoadLocation("local")
	birthDay, _ := time.ParseInLocation("2006-01-12", UpdateUserForm.Birthday, loc)
	_, err := global.UserSrvClient.UpdateUser(context.Background(), &proto.UpdateUserInfo{
		Id:       int32(currentUser.ID),
		NickName: UpdateUserForm.Name,
		Gender:   UpdateUserForm.Gender,
		BirthDay: uint64(birthDay.Unix()),
	})
	if err != nil {
		HandleGrpcErrorToHttp(err, ctx)
		return
	}
	ctx.JSON(http.StatusOK, gin.H{}) 
}
